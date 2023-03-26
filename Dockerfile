FROM owasp/zap2docker-weekly

USER zap
COPY mass-base* /zap/

RUN echo "alias ll='ls -la'" >> ~/.bash_aliases

USER root
RUN chown zap /zap/mass-base*
