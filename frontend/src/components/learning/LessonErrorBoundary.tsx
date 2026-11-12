import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = {
  children: ReactNode;
  onReset: () => void;
};

type State = {
  error: Error | null;
};

export default class LessonErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[LessonErrorBoundary] Lesson UI crashed", error, info);
  }

  private reset = () => {
    this.setState({ error: null });
    this.props.onReset();
  };

  render() {
    if (!this.state.error) return this.props.children;

    return <section className="mx-auto my-8 grid max-w-3xl gap-3 rounded-2xl border border-danger/40 bg-surface p-5" role="alert">
      <span className="text-xs font-semibold tracking-[0.12em] text-danger uppercase">Có lỗi hiển thị</span>
      <h2 className="font-display text-2xl font-semibold">Không thể hiển thị đầy đủ bài học</h2>
      <p>Một thành phần giao diện của bài học gặp lỗi. HarmonyMentor đã giữ ứng dụng hoạt động thay vì để toàn trang trắng.</p>
      <details>
        <summary className="cursor-pointer text-sm text-muted">Thông tin để báo cho nhóm phát triển</summary>
        <code className="mt-2 block font-mono text-sm break-words whitespace-pre-wrap">{this.state.error.message}</code>
      </details>
      <button type="button" className="min-h-11 justify-self-start rounded-lg bg-primary px-4 font-semibold text-white hover:bg-primary-strong" onClick={this.reset}>Quay lại danh sách bài học</button>
    </section>;
  }
}
