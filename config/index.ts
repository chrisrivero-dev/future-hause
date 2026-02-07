import { RuntimeMode, DEFAULT_RUNTIME_MODE } from './runtime';

const envMode = process.env.FUTURE_HAUSE_RUNTIME_MODE;

const runtimeMode: RuntimeMode =
  envMode === 'LOCAL' ||
  envMode === 'WORK_REMOTE' ||
  envMode === 'DEMO' ||
  envMode === 'AIRPLANE'
    ? envMode
    : DEFAULT_RUNTIME_MODE;

export const config = Object.freeze({
  appName: 'Future Hause',
  version: '0.1.0',
  runtimeMode,
});
