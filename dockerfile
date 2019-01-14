# 2018-12-25 15:29:07
# Version: 0.1
# tcp2http

FROM chenwx716/bmgr_platform:1.0.0

LABEL author="chenwx"
LABEL version="0.1"

# add bmgr server
ADD http_server.py /usr/local/

# CMD
CMD python3 /usr/local/http_server.py

EXPOSE 19001
