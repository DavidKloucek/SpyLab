import { defineConfig } from 'orval';

export default defineConfig({
    api: {
        input: 'http://localhost:8000/openapi.json',
        output: {
            target: 'src/api/generated.ts',
            client: "fetch",
            prettier: true,
        },
    },
});
