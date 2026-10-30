ARG NODE_RED_IMAGE=nodered/node-red:4.1.0
FROM ${NODE_RED_IMAGE}

# Install outside /data: its persistent volume must not hide the extra nodes.
USER root
WORKDIR /usr/src/node-red
RUN npm install --omit=dev --no-audit --no-fund node-red-contrib-influxdb@0.7.0
COPY --chown=node-red:root flows.json /data/flows.json
USER node-red
