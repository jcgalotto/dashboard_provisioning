FROM node:20-alpine
WORKDIR /app
COPY package.json tsconfig.json tsconfig.node.json vite.config.ts tailwind.config.js postcss.config.js index.html ./
COPY src ./src
RUN npm install --ignore-scripts && npm run build
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
