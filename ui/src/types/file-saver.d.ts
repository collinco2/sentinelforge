declare module "file-saver" {
  export function saveAs(
    data: Blob | File | string,
    filename?: string,
    options?: { type?: string; autoBom?: boolean },
  ): void;
}
