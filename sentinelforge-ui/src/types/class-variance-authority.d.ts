declare module "class-variance-authority" {
  export type VariantProps<T extends (...args: any) => any> = Parameters<T>[0];

  export function cva(
    base?: string,
    config?: {
      variants?: Record<string, Record<string, string>>;
      compoundVariants?: Array<Record<string, any> & { class: string }>;
      defaultVariants?: Record<string, string>;
    },
  ): (props?: Record<string, any>) => string;
}
