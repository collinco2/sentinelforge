declare module "markdown-it" {
  interface MarkdownIt {
    render(markdown: string): string;
  }

  interface MarkdownItConstructor {
    new (): MarkdownIt;
    (): MarkdownIt;
  }

  const MarkdownIt: MarkdownItConstructor;

  export = MarkdownIt;
}
