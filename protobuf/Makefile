#
# Makefile to call protocol buffer compiler for Java/Python
#

CC          :=protoc
SRC         :=proto_message.proto

PYTHON_NAME :=proto_message_pb2.py
PYTHON_STUB_NAME :=proto_message_pb2.pyi
JAVA_NAME :=ProtoMessage.java

PYTHON_RELATIVE_DEST_DIR := ../gym-diplomacy/gym_diplomacy/envs
JAVA_RELATIVE_DEST_DIR   := ../bandana/src/main/java

JAVA_PACKAGE := cruz/agents

PYTHON_OUT		:= $(PYTHON_RELATIVE_DEST_DIR)/$(PYTHON_NAME)
PYTHON_STUB_OUT := $(PYTHON_RELATIVE_DEST_DIR)/$(PYTHON_STUB_NAME)
JAVA_OUT        := $(JAVA_RELATIVE_DEST_DIR)/$(JAVA_PACKAGE)/$(JAVA_NAME)

all: $(PYTHON_OUT) $(JAVA_OUT)

$(PYTHON_OUT) $(PYTHON_STUB_OUT): $(SRC)
	$(CC) $(SRC) --plugin=protoc-gen-mypy=./protoc-gen-mypy --python_out=$(PYTHON_RELATIVE_DEST_DIR) --mypy_out=$(PYTHON_RELATIVE_DEST_DIR)
$(JAVA_OUT): $(SRC)
	$(CC) $(SRC) --java_out=$(JAVA_RELATIVE_DEST_DIR)

clean:
	$(RM) $(PYTHON_OUT)
	$(RM) $(PYTHON_STUB_OUT)
	$(RM) $(JAVA_OUT)
