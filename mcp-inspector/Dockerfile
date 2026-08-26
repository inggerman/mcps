FROM node:22-slim

WORKDIR /app

RUN npm install -g @modelcontextprotocol/inspector@latest

ENV HOST=0.0.0.0
ENV CLIENT_PORT=8000
ENV SERVER_PORT=8001
ENV DANGEROUSLY_BIND_ALL_INTERFACES=true
ENV BROWSER=none
ENV SHELL=/bin/sh
EXPOSE 8000 8001

CMD ["npx", "@modelcontextprotocol/inspector", "--port", "8000", "--host", "0.0.0.0"]
