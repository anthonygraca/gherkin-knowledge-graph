// Minimal catalog used by this project's own step definitions. No CTA dependency.
export class Catalog {
  constructor(entries = []) {
    this.entries = new Map(entries.map((entry) => [entry.title, { ...entry }]));
  }

  publish(title, body = '') {
    if (!title || !title.trim()) {
      throw new Error('title is required');
    }
    this.entries.set(title, { title, body, published: true });
  }

  draft(title) {
    this.entries.set(title, { title, published: false });
  }

  visible() {
    return [...this.entries.values()].filter((entry) => entry.published).map((e) => e.title);
  }

  search(term) {
    const needle = term.toLowerCase();
    return this.visible().filter((title) => title.toLowerCase().includes(needle));
  }
}
