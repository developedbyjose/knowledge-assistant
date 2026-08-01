FROM node:22-alpine

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

RUN corepack enable && corepack prepare pnpm@10.14.0 --activate

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

EXPOSE 3000

CMD ["pnpm", "dev", "--hostname", "0.0.0.0", "--port", "3000"]
