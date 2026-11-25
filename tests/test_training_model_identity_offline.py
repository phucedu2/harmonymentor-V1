"""Offline checks of the training script's model identity guard."""
import ast
from pathlib import Path
import re
import types
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'ai' / 'hm_training' / 'train_qlora.py'
tree = ast.parse(SCRIPT.read_text(encoding='utf-8'))
functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {'validate_model_selection', 'verify_loaded_identity'}]
namespace = {'re': re}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(SCRIPT), 'exec'), namespace)
validate = namespace['validate_model_selection']
verify = namespace['verify_loaded_identity']
SHA = 'a' * 40
REPO = 'unsloth/example'

class IdentityGuardTests(unittest.TestCase):
    def objects(self, model_sha=SHA, token_sha=SHA, model_repo=REPO, token_repo=REPO):
        return (types.SimpleNamespace(config=types.SimpleNamespace(_commit_hash=model_sha, _name_or_path=model_repo)),
                types.SimpleNamespace(init_kwargs={'_commit_hash': token_sha, 'name_or_path': token_repo}))
    def test_valid(self):
        validate(REPO, SHA)
        verify(*self.objects(), REPO, SHA)
    def test_bad_selection(self):
        for repo, sha in [('/tmp/model', SHA), (REPO, ''), (REPO, 'main'), (REPO, 'A'*40)]:
            with self.subTest(repo=repo, sha=sha), self.assertRaises(SystemExit): validate(repo, sha)
    def test_revision_mismatch_or_missing(self):
        for model_sha, token_sha in [(None, SHA), (SHA, None), ('b'*40, SHA), (SHA, 'b'*40)]:
            with self.subTest(model_sha=model_sha, token_sha=token_sha), self.assertRaises(SystemExit):
                verify(*self.objects(model_sha=model_sha, token_sha=token_sha), REPO, SHA)
    def test_repository_mismatch_or_missing(self):
        for model_repo, token_repo in [(None, REPO), (REPO, None), ('other/model', REPO), (REPO, 'other/model')]:
            with self.subTest(model_repo=model_repo, token_repo=token_repo), self.assertRaises(SystemExit):
                verify(*self.objects(model_repo=model_repo, token_repo=token_repo), REPO, SHA)
    def test_call_and_guard_order(self):
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        calls = [n for n in ast.walk(main) if isinstance(n, ast.Call)]
        loader = next(n for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == 'from_pretrained')
        keywords = {k.arg: k.value for k in loader.keywords}
        self.assertIs(keywords['trust_remote_code'].value, False)
        self.assertEqual(ast.unparse(keywords['revision']), 'args.model_revision')
        guard = next(n for n in calls if isinstance(n.func, ast.Name) and n.func.id == 'verify_loaded_identity')
        adapter = next(n for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == 'get_peft_model')
        self.assertLess(loader.lineno, guard.lineno)
        self.assertLess(guard.lineno, adapter.lineno)

if __name__ == '__main__': unittest.main()
