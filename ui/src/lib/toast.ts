// Simple toast implementation
// In a real app, you would use a library like sonner or react-hot-toast

interface ToastOptions {
  duration?: number;
}

type ToastType = 'success' | 'error' | 'info';
type Toast = { id: string; message: string; type: ToastType };

class ToastManager {
  private toasts: Array<Toast> = [];
  private listeners: Array<(toasts: Toast[]) => void> = [];

  private notify() {
    this.listeners.forEach(listener => listener([...this.toasts]));
  }

  private addToast(message: string, type: 'success' | 'error' | 'info', options: ToastOptions = {}) {
    const id = Math.random().toString(36).substr(2, 9);
    const toast = { id, message, type };
    
    this.toasts.push(toast);
    this.notify();

    // Auto remove after duration
    setTimeout(() => {
      this.toasts = this.toasts.filter(t => t.id !== id);
      this.notify();
    }, options.duration || 3000);

    return id;
  }

  success(message: string, options?: ToastOptions) {
    return this.addToast(message, 'success', options);
  }

  error(message: string, options?: ToastOptions) {
    return this.addToast(message, 'error', options);
  }

  info(message: string, options?: ToastOptions) {
    return this.addToast(message, 'info', options);
  }

  subscribe(listener: (toasts: typeof this.toasts) => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  getToasts() {
    return [...this.toasts];
  }
}

export const toast = new ToastManager();
