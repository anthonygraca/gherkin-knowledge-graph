/**
 * Opt-in live local-model acceptance run (AI-02 SCN-3205).
 *
 * Run under an OS-level network denial, for example:
 *   unshare -rn env CTA_EGRESS_DENIED=1 CTA_LOCAL_EMBEDDING_MODEL_DIR=... \
 *     npx cucumber-js --config cucumber.live.mjs
 */
import base from './cucumber.mjs';

export default {
  ...base,
  tags: '@live-local',
  format: ['summary', 'message:reports/cucumber-live-messages.ndjson'],
  formatOptions: { snippetInterface: 'async-await' },
};
