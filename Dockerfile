FROM node:13.12-buster-slim AS jsdeps

RUN apt update -y
RUN apt install  -y g++ build-essential python3

COPY . .

RUN npm install && npm run build


FROM python:3.8-slim-buster

LABEL maintainer="webops@digital.trade.gov.uk"

ENV DJANGO_SETTINGS_MODULE "settings"

# add git client
RUN apt-get -qq update && apt-get install --no-install-recommends -qqy \
    curl \
    ca-certificates \
    git

# don't run as root
RUN groupadd -g 1000 tamato && \
    useradd -u 1000 -g tamato -m tamato
USER tamato

RUN mkdir /home/tamato/app
WORKDIR /home/tamato/app

# install python dependencies
COPY requirements.txt ./
RUN pip install -U pip && \
    pip install -r requirements.txt --no-warn-script-location

COPY --chown=tamato:tamato . .
COPY --chown=tamato:tamato --from=jsdeps node_modules/govuk-frontend/govuk node_modules/govuk-frontend/govuk
COPY --chown=tamato:tamato --from=jsdeps static/webpack_bundles static/webpack_bundles
COPY --chown=tamato:tamato --from=jsdeps webpack-stats.json ./

# empty .env file to prevent warning messages
RUN touch .env

# collect static files for deployment
RUN python manage.py collectstatic --noinput

ADD ./ /home/tamato/app/

EXPOSE 8000
CMD ["/home/tamato/.local/bin/gunicorn", "-b", "0.0.0.0:8000", "-w", "1", "wsgi:application"]
