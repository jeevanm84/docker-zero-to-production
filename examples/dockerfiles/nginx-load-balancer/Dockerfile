# Nginx configured as a load balancer in front of the three flask-app
# backends. `daemon off;` (already the default CMD below via -g) keeps
# Nginx as PID 1 so the container stays alive — see docs/TROUBLESHOOTING.md #1.

FROM nginx:latest

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
