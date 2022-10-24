FROM ubuntu:21.10

ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt -y update && \
    apt -y upgrade && \
    apt install --install-recommends -y wget python3 python3-pip g++ upx unzip git

RUN wget https://github.com/JPCERTCC/upx-mod/releases/download/v4.00-beta/upx_mod-amd64_linux.tar.xz && \
    tar Jxfv upx_mod-amd64_linux.tar.xz && \
		chmod 755 upx-mod && \
		mv upx-mod /bin

RUN wget https://github.com/mandiant/flare-floss/releases/download/v2.0.0/floss-v2.0.0-linux.zip && \
    unzip floss-v2.0.0-linux.zip && \
    chmod 755 floss && \
    mv floss /bin

RUN wget https://github.com/mandiant/capa/releases/download/v3.2.0/capa-v3.2.0-linux.zip && \
    unzip capa-v3.2.0-linux.zip && \
    chmod 755 capa && \
    mv capa /bin

RUN pip install yara-python pyzipper GitPython oletools stringsifter

RUN wget https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -O awscliv2.zip && \
    unzip awscliv2.zip && \
    ./aws/install

RUN git clone https://github.com/Neo23x0/yarGen.git && \
    cd yarGen && \
    pip install -r requirements.txt && \
    python3 yarGen.py --update

# for stringsifter bug https://github.com/mandiant/stringsifter/issues/18
RUN pip install lightgbm==3.3.0

RUN rm -rf /capa-v3.2.0-linux.zip && \
    rm -rf /awscliv2.zip && \
    rm -rf /floss-v2.0.0-linux.zip

COPY run.sh /tmp

RUN chmod +x /tmp/run.sh

WORKDIR /tmp

CMD /bin/bash
