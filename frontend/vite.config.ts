import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    babel({ presets: [reactCompilerPreset()] })
  ],
  server: {
    // Docker on Windows doesn't forward file-change events into the container, so poll instead
    watch: {
      usePolling: process.env.VITE_USE_POLLING === 'true',
      interval: 300,
    },
  },
})
