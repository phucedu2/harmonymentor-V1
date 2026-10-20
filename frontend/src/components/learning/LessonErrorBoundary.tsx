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

    return <section className="lesson-crash-fallback" role="alert">
      <span className="eyebrow">LESSON RECOVERY</span>
      <h2>Không thể hiển thị đầy đủ bài học</h2>
      <p>Một thành phần giao diện của bài học gặp lỗi. HarmonyMentor đã giữ ứng dụng hoạt động thay vì để toàn trang trắng.</p>
      <details>
        <summary>Chi tiết kỹ thuật</summary>
        <code>{this.state.error.message}</code>
      </details>
      <button type="button" onClick={this.reset}>Quay lại danh sách bài học</button>
    </section>;
  }
}
