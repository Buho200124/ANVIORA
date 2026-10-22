FROM nginx:1.27-alpine

COPY gateway/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend /usr/share/nginx/html
# Nginx corre sin privilegios: los archivos estáticos deben ser legibles por cualquiera
RUN chmod -R a+rX /usr/share/nginx/html

EXPOSE 80
