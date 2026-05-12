import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',  //Se pone para que funcione en Docker
    port: 5173, 
    watch:{
      usePolling: true //Se usa esto para que se pueda recargar los cambios en hot reload
    },
  },
})
