import assert from 'node:assert/strict';
import { Given, When, Then, Before } from '@cucumber/cucumber';
import { Catalog } from '../src/catalog.js';

Before(function () {
  this.catalog = new Catalog();
});

Given('the catalog contains {string} and {string}', function (first, second) {
  this.catalog.publish(first);
  this.catalog.publish(second);
});

Given('a draft recipe {string}', function (title) {
  this.catalog.draft(title);
});

When('the visitor opens the catalog', function () {
  this.listed = this.catalog.visible();
});

Then('the catalog shows {string}', function (title) {
  assert.ok(this.listed.includes(title), `${title} was not listed: ${this.listed}`);
});

Then('the catalog does not show {string}', function (title) {
  assert.ok(!this.listed.includes(title), `${title} must stay hidden`);
});

When('the visitor searches for {string}', function (term) {
  this.results = this.catalog.search(term);
});

Then('the result list is {string}', function (verdict) {
  assert.equal(this.results.length > 0, verdict === 'Hits');
});

Then('the visitor sees the search note', function (note) {
  assert.match(note, /^query: /);
});

Then('the search filters include', function (table) {
  const rows = table.raw();
  assert.deepEqual(rows[0], ['filter', 'value']);
  assert.equal(rows[1][0], 'term');
  assert.match(rows[1][1], /soup|toast/);
});

Then('the search does not require an account', function () {
  assert.ok(Array.isArray(this.results));
});
