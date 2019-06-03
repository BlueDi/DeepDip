# Makefile to call protocol buffer compiler for Java/Python

CC := protoc
SRC := gym_diplomacy/envs/proto_message.proto

PYTHON_NAME := proto_message_pb2.py
PYTHON_STUB_NAME := proto_message_pb2.pyi
PYTHON_GRPC_NAME := proto_message_pb2_grpc.py
JAVA_NAME := ProtoMessage.java

PYTHON_RELATIVE_DEST_DIR := ../gym-diplomacy/gym_diplomacy/envs
PYTHON_WEIRD_RELATIVE_DEST_DIR := ../gym-diplomacy	
JAVA_RELATIVE_DEST_DIR   := ../bandana/src/main/java

JAVA_PACKAGE := cruz/agents

PYTHON_OUT		:= $(PYTHON_RELATIVE_DEST_DIR)/$(PYTHON_NAME)
PYTHON_STUB_OUT := $(PYTHON_RELATIVE_DEST_DIR)/$(PYTHON_STUB_NAME)
PYTHON_GRPC_OUT := $(PYTHON_RELATIVE_DEST_DIR)/$(PYTHON_GRPC_NAME)
JAVA_OUT        := $(JAVA_RELATIVE_DEST_DIR)/$(JAVA_PACKAGE)/$(JAVA_NAME)
JAVA_GRPC_OUT   := $(wildcard $(JAVA_RELATIVE_DEST_DIR)/$(JAVA_PACKAGE)/*Grpc.java)

all: $(PYTHON_OUT) $(JAVA_OUT)

$(PYTHON_OUT) $(PYTHON_STUB_OUT) $(PYTHON_GRPC_OUT): $(SRC)
	$(CC) $(SRC) --plugin=protoc-gen-mypy=./protoc-gen-mypy \
	--plugin=protoc-gen-grpc_python=./grpc_python_plugin \
	--grpc_python_out=$(PYTHON_WEIRD_RELATIVE_DEST_DIR) \
    --python_out=$(PYTHON_WEIRD_RELATIVE_DEST_DIR) \
    --mypy_out=$(PYTHON_WEIRD_RELATIVE_DEST_DIR)

$(JAVA_OUT) $(JAVA_GRPC_OUT): $(SRC)
	$(CC) $(SRC) --plugin=protoc-gen-grpc-java=./protoc-gen-grpc-java-1.20.0-linux-x86_64.exe \
	--grpc-java_out=$(JAVA_RELATIVE_DEST_DIR) \
	--java_out=$(JAVA_RELATIVE_DEST_DIR)

clean:
	$(RM) $(PYTHON_OUT)
	$(RM) $(PYTHON_STUB_OUT)
	$(RM) $(PYTHON_GRPC_OUT)
	$(RM) $(JAVA_OUT)
	$(RM) $(JAVA_GRPC_OUT)

