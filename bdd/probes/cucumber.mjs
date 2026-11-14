// Minimal configuration for harness probes: no main-suite imports or paths. The probe runner passes
// its own --import and feature path, so a probe can never re-enter the acceptance suite.
export default {
  import: [],
  paths: [],
  format: [],
  parallel: 1,
  retry: 0,
};
