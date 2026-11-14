// This hook would create a sentinel file if the twin suite were ever executed. CTA indexes the
// repository read-only and must never run it.
import { writeFileSync } from 'node:fs';
import { Before } from '@cucumber/cucumber';

Before(function () {
  writeFileSync('sentinel.txt', 'the twin suite executed');
});
