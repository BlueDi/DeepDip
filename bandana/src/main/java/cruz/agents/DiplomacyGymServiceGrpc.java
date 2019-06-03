package cruz.agents;

import static io.grpc.MethodDescriptor.generateFullMethodName;
import static io.grpc.stub.ClientCalls.asyncBidiStreamingCall;
import static io.grpc.stub.ClientCalls.asyncClientStreamingCall;
import static io.grpc.stub.ClientCalls.asyncServerStreamingCall;
import static io.grpc.stub.ClientCalls.asyncUnaryCall;
import static io.grpc.stub.ClientCalls.blockingServerStreamingCall;
import static io.grpc.stub.ClientCalls.blockingUnaryCall;
import static io.grpc.stub.ClientCalls.futureUnaryCall;
import static io.grpc.stub.ServerCalls.asyncBidiStreamingCall;
import static io.grpc.stub.ServerCalls.asyncClientStreamingCall;
import static io.grpc.stub.ServerCalls.asyncServerStreamingCall;
import static io.grpc.stub.ServerCalls.asyncUnaryCall;
import static io.grpc.stub.ServerCalls.asyncUnimplementedStreamingCall;
import static io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.20.0)",
    comments = "Source: gym_diplomacy/envs/proto_message.proto")
public final class DiplomacyGymServiceGrpc {

  private DiplomacyGymServiceGrpc() {}

  public static final String SERVICE_NAME = "dip_q.DiplomacyGymService";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<cruz.agents.ProtoMessage.BandanaRequest,
      cruz.agents.ProtoMessage.DiplomacyGymResponse> getGetActionMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetAction",
      requestType = cruz.agents.ProtoMessage.BandanaRequest.class,
      responseType = cruz.agents.ProtoMessage.DiplomacyGymResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<cruz.agents.ProtoMessage.BandanaRequest,
      cruz.agents.ProtoMessage.DiplomacyGymResponse> getGetActionMethod() {
    io.grpc.MethodDescriptor<cruz.agents.ProtoMessage.BandanaRequest, cruz.agents.ProtoMessage.DiplomacyGymResponse> getGetActionMethod;
    if ((getGetActionMethod = DiplomacyGymServiceGrpc.getGetActionMethod) == null) {
      synchronized (DiplomacyGymServiceGrpc.class) {
        if ((getGetActionMethod = DiplomacyGymServiceGrpc.getGetActionMethod) == null) {
          DiplomacyGymServiceGrpc.getGetActionMethod = getGetActionMethod = 
              io.grpc.MethodDescriptor.<cruz.agents.ProtoMessage.BandanaRequest, cruz.agents.ProtoMessage.DiplomacyGymResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(
                  "dip_q.DiplomacyGymService", "GetAction"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  cruz.agents.ProtoMessage.BandanaRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  cruz.agents.ProtoMessage.DiplomacyGymResponse.getDefaultInstance()))
                  .setSchemaDescriptor(new DiplomacyGymServiceMethodDescriptorSupplier("GetAction"))
                  .build();
          }
        }
     }
     return getGetActionMethod;
  }

  private static volatile io.grpc.MethodDescriptor<cruz.agents.ProtoMessage.BandanaRequest,
      cruz.agents.ProtoMessage.DiplomacyGymOrdersResponse> getGetStrategyActionMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetStrategyAction",
      requestType = cruz.agents.ProtoMessage.BandanaRequest.class,
      responseType = cruz.agents.ProtoMessage.DiplomacyGymOrdersResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<cruz.agents.ProtoMessage.BandanaRequest,
      cruz.agents.ProtoMessage.DiplomacyGymOrdersResponse> getGetStrategyActionMethod() {
    io.grpc.MethodDescriptor<cruz.agents.ProtoMessage.BandanaRequest, cruz.agents.ProtoMessage.DiplomacyGymOrdersResponse> getGetStrategyActionMethod;
    if ((getGetStrategyActionMethod = DiplomacyGymServiceGrpc.getGetStrategyActionMethod) == null) {
      synchronized (DiplomacyGymServiceGrpc.class) {
        if ((getGetStrategyActionMethod = DiplomacyGymServiceGrpc.getGetStrategyActionMethod) == null) {
          DiplomacyGymServiceGrpc.getGetStrategyActionMethod = getGetStrategyActionMethod = 
              io.grpc.MethodDescriptor.<cruz.agents.ProtoMessage.BandanaRequest, cruz.agents.ProtoMessage.DiplomacyGymOrdersResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(
                  "dip_q.DiplomacyGymService", "GetStrategyAction"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  cruz.agents.ProtoMessage.BandanaRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  cruz.agents.ProtoMessage.DiplomacyGymOrdersResponse.getDefaultInstance()))
                  .setSchemaDescriptor(new DiplomacyGymServiceMethodDescriptorSupplier("GetStrategyAction"))
                  .build();
          }
        }
     }
     return getGetStrategyActionMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static DiplomacyGymServiceStub newStub(io.grpc.Channel channel) {
    return new DiplomacyGymServiceStub(channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static DiplomacyGymServiceBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    return new DiplomacyGymServiceBlockingStub(channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static DiplomacyGymServiceFutureStub newFutureStub(
      io.grpc.Channel channel) {
    return new DiplomacyGymServiceFutureStub(channel);
  }

  /**
   */
  public static abstract class DiplomacyGymServiceImplBase implements io.grpc.BindableService {

    /**
     */
    public void getAction(cruz.agents.ProtoMessage.BandanaRequest request,
        io.grpc.stub.StreamObserver<cruz.agents.ProtoMessage.DiplomacyGymResponse> responseObserver) {
      asyncUnimplementedUnaryCall(getGetActionMethod(), responseObserver);
    }

    /**
     */
    public void getStrategyAction(cruz.agents.ProtoMessage.BandanaRequest request,
        io.grpc.stub.StreamObserver<cruz.agents.ProtoMessage.DiplomacyGymOrdersResponse> responseObserver) {
      asyncUnimplementedUnaryCall(getGetStrategyActionMethod(), responseObserver);
    }

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return io.grpc.ServerServiceDefinition.builder(getServiceDescriptor())
          .addMethod(
            getGetActionMethod(),
            asyncUnaryCall(
              new MethodHandlers<
                cruz.agents.ProtoMessage.BandanaRequest,
                cruz.agents.ProtoMessage.DiplomacyGymResponse>(
                  this, METHODID_GET_ACTION)))
          .addMethod(
            getGetStrategyActionMethod(),
            asyncUnaryCall(
              new MethodHandlers<
                cruz.agents.ProtoMessage.BandanaRequest,
                cruz.agents.ProtoMessage.DiplomacyGymOrdersResponse>(
                  this, METHODID_GET_STRATEGY_ACTION)))
          .build();
    }
  }

  /**
   */
  public static final class DiplomacyGymServiceStub extends io.grpc.stub.AbstractStub<DiplomacyGymServiceStub> {
    private DiplomacyGymServiceStub(io.grpc.Channel channel) {
      super(channel);
    }

    private DiplomacyGymServiceStub(io.grpc.Channel channel,
        io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected DiplomacyGymServiceStub build(io.grpc.Channel channel,
        io.grpc.CallOptions callOptions) {
      return new DiplomacyGymServiceStub(channel, callOptions);
    }

    /**
     */
    public void getAction(cruz.agents.ProtoMessage.BandanaRequest request,
        io.grpc.stub.StreamObserver<cruz.agents.ProtoMessage.DiplomacyGymResponse> responseObserver) {
      asyncUnaryCall(
          getChannel().newCall(getGetActionMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void getStrategyAction(cruz.agents.ProtoMessage.BandanaRequest request,
        io.grpc.stub.StreamObserver<cruz.agents.ProtoMessage.DiplomacyGymOrdersResponse> responseObserver) {
      asyncUnaryCall(
          getChannel().newCall(getGetStrategyActionMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   */
  public static final class DiplomacyGymServiceBlockingStub extends io.grpc.stub.AbstractStub<DiplomacyGymServiceBlockingStub> {
    private DiplomacyGymServiceBlockingStub(io.grpc.Channel channel) {
      super(channel);
    }

    private DiplomacyGymServiceBlockingStub(io.grpc.Channel channel,
        io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected DiplomacyGymServiceBlockingStub build(io.grpc.Channel channel,
        io.grpc.CallOptions callOptions) {
      return new DiplomacyGymServiceBlockingStub(channel, callOptions);
    }

    /**
     */
    public cruz.agents.ProtoMessage.DiplomacyGymResponse getAction(cruz.agents.ProtoMessage.BandanaRequest request) {
      return blockingUnaryCall(
          getChannel(), getGetActionMethod(), getCallOptions(), request);
    }

    /**
     */
    public cruz.agents.ProtoMessage.DiplomacyGymOrdersResponse getStrategyAction(cruz.agents.ProtoMessage.BandanaRequest request) {
      return blockingUnaryCall(
          getChannel(), getGetStrategyActionMethod(), getCallOptions(), request);
    }
  }

  /**
   */
  public static final class DiplomacyGymServiceFutureStub extends io.grpc.stub.AbstractStub<DiplomacyGymServiceFutureStub> {
    private DiplomacyGymServiceFutureStub(io.grpc.Channel channel) {
      super(channel);
    }

    private DiplomacyGymServiceFutureStub(io.grpc.Channel channel,
        io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected DiplomacyGymServiceFutureStub build(io.grpc.Channel channel,
        io.grpc.CallOptions callOptions) {
      return new DiplomacyGymServiceFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<cruz.agents.ProtoMessage.DiplomacyGymResponse> getAction(
        cruz.agents.ProtoMessage.BandanaRequest request) {
      return futureUnaryCall(
          getChannel().newCall(getGetActionMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<cruz.agents.ProtoMessage.DiplomacyGymOrdersResponse> getStrategyAction(
        cruz.agents.ProtoMessage.BandanaRequest request) {
      return futureUnaryCall(
          getChannel().newCall(getGetStrategyActionMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_GET_ACTION = 0;
  private static final int METHODID_GET_STRATEGY_ACTION = 1;

  private static final class MethodHandlers<Req, Resp> implements
      io.grpc.stub.ServerCalls.UnaryMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ServerStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ClientStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.BidiStreamingMethod<Req, Resp> {
    private final DiplomacyGymServiceImplBase serviceImpl;
    private final int methodId;

    MethodHandlers(DiplomacyGymServiceImplBase serviceImpl, int methodId) {
      this.serviceImpl = serviceImpl;
      this.methodId = methodId;
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public void invoke(Req request, io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        case METHODID_GET_ACTION:
          serviceImpl.getAction((cruz.agents.ProtoMessage.BandanaRequest) request,
              (io.grpc.stub.StreamObserver<cruz.agents.ProtoMessage.DiplomacyGymResponse>) responseObserver);
          break;
        case METHODID_GET_STRATEGY_ACTION:
          serviceImpl.getStrategyAction((cruz.agents.ProtoMessage.BandanaRequest) request,
              (io.grpc.stub.StreamObserver<cruz.agents.ProtoMessage.DiplomacyGymOrdersResponse>) responseObserver);
          break;
        default:
          throw new AssertionError();
      }
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public io.grpc.stub.StreamObserver<Req> invoke(
        io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        default:
          throw new AssertionError();
      }
    }
  }

  private static abstract class DiplomacyGymServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    DiplomacyGymServiceBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return cruz.agents.ProtoMessage.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("DiplomacyGymService");
    }
  }

  private static final class DiplomacyGymServiceFileDescriptorSupplier
      extends DiplomacyGymServiceBaseDescriptorSupplier {
    DiplomacyGymServiceFileDescriptorSupplier() {}
  }

  private static final class DiplomacyGymServiceMethodDescriptorSupplier
      extends DiplomacyGymServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final String methodName;

    DiplomacyGymServiceMethodDescriptorSupplier(String methodName) {
      this.methodName = methodName;
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.MethodDescriptor getMethodDescriptor() {
      return getServiceDescriptor().findMethodByName(methodName);
    }
  }

  private static volatile io.grpc.ServiceDescriptor serviceDescriptor;

  public static io.grpc.ServiceDescriptor getServiceDescriptor() {
    io.grpc.ServiceDescriptor result = serviceDescriptor;
    if (result == null) {
      synchronized (DiplomacyGymServiceGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new DiplomacyGymServiceFileDescriptorSupplier())
              .addMethod(getGetActionMethod())
              .addMethod(getGetStrategyActionMethod())
              .build();
        }
      }
    }
    return result;
  }
}
