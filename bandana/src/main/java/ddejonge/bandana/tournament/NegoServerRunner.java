package ddejonge.bandana.tournament;

import java.io.File;

import ddejonge.bandana.negoProtocol.DiplomacyProtocolManager;
import ddejonge.negoServer.Logger;
import ddejonge.negoServer.NegotiationServer;



public class NegoServerRunner {


	
	public static int DEFAULT_SERVER_PORT = 16714;
	public static String DEFAULT_LOG_FOLDER_PATH = "log" + File.separator + Logger.getDateString() + File.separator; 
	public static boolean ALLOW_INFORMAL_MESSAGES = true;
	
	/**If set to true the ProtocolManager will only confirm proposals if they are consistent with all proposals that have been confirmed earlier.*/
	public static boolean ENABLE_CONSISTENCY_CHECKING = true;
	
	private static NegotiationServer negoServer = null;
	
	private static DiplomacyProtocolManager diplomacyProtocolManager;
	
	public static void run(TournamentObserver tournamentObserver, int numberOfGames){
		run(tournamentObserver, DEFAULT_SERVER_PORT, DEFAULT_LOG_FOLDER_PATH, numberOfGames);
	}
	
	public static void run(TournamentObserver tournamentObserver, int port, int numberOfGames){
		run(tournamentObserver, port, DEFAULT_LOG_FOLDER_PATH, numberOfGames);
	}
	
	public static void run(TournamentObserver tournamentObserver, String logFolderPath, int numberOfGames){
		run(tournamentObserver, DEFAULT_SERVER_PORT, logFolderPath, numberOfGames);
	}

	
	public static void run(TournamentObserver tournamentObserver, int port, String logFolderPath, int numberOfGames){
		
		
		diplomacyProtocolManager = new DiplomacyProtocolManager(tournamentObserver, logFolderPath);
		diplomacyProtocolManager.allowInformalMessages(ALLOW_INFORMAL_MESSAGES);
		diplomacyProtocolManager.enableConsistencyChecking(ENABLE_CONSISTENCY_CHECKING);
		
		//Set up a negotiation server.
		negoServer = new NegotiationServer(diplomacyProtocolManager);
		negoServer.setPortNumber(port);
		negoServer.enableLogging(logFolderPath, "NegotiationServer.log");
		negoServer.startServerInNewThread();
		
	
		System.out.println();
		System.out.println("Negotiation Sever started!");
		System.out.println();
	}
	
	/**
	 * This method must be call at the start of every new game, before the players are started.
	 * @param gameID
	 */
	public static void notifyNewGame(int gameID){
		if(diplomacyProtocolManager != null){
			diplomacyProtocolManager.notifyNewGame(gameID);
		}
	}

	public static void stop(){
		
		if(diplomacyProtocolManager != null){
			diplomacyProtocolManager.stop();
		}
		
		if(negoServer != null){
			negoServer.stopServer();
		}
		
	}
}
