import assert from 'node:assert/strict';
import { Given, When, Then } from '@cucumber/cucumber';

Given('an author with a draft recipe', function () {
  this.draft = { title: '' };
});

When('the author publishes it without a title', function () {
  try {
    if (!this.draft.title) throw new Error('title is required');
    this.error = null;
  } catch (error) {
    this.error = error;
  }
});

Then('publication is rejected with {string}', function (message) {
  assert.ok(this.error, 'expected publication to be rejected');
  assert.match(this.error.message, new RegExp(message));
});
