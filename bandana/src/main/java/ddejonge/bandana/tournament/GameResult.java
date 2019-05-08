package ddejonge.bandana.tournament;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Arrays;

public class GameResult implements Serializable{

	private static final long serialVersionUID = 1L;

	/**
	 * 
	 * SOLO: the player achieved a solo victory.<br/>
	 * DRAW: the player did not get eliminated and no other power achieved a solo victory.<br/>
	 * LOST: the player lost because another power achieved a solo victory.<br/>
	 * ELIMINATED: the player lost all its supply centers before the end of the game.
	 * 
	 * @author Dave de Jonge
	 *
	 */
	public enum PlayerResult {
	    ELIMINATED, LOST, DRAW, SOLO
	}
	
	
	private int numberOfPlayers;
	private String[] powers;
	private String[] names;
	private int[] numSCs;				//number of SCs at the end of the game.
	private int[] yearOfElimination ;   //if a power is not eliminated, its year of elimination is 0.
	
	private boolean endedInSolo = false;
	private int numSurvivors = 0;
	
	private PlayerResult[] playerResults;
	
	int[] rank2playerNumber = null;
	
	/**
	 * maps each player index to its rank, taking into account that several players may end equally.
	 * For example, if two players together share the first place, then they both have a precise rank of 1.5 
	 */
	double[] playerNumber2preciseRank;
	
	/**
	 * 
	 * @param smrMessage
	 * @param numberOfPlayers The number of participants.
	 */
	public GameResult(String[] smrMessage, int numberOfPlayers){

		// JC: Creating everything with the newly added number of players
		this.numberOfPlayers = numberOfPlayers;

		this.powers = new String[this.numberOfPlayers];
		this.names = new String[this.numberOfPlayers];
		this.numSCs = new int[this.numberOfPlayers];
		this.yearOfElimination = new int[this.numberOfPlayers];
		this.playerResults = new PlayerResult[this.numberOfPlayers];
		this.playerNumber2preciseRank = new double[this.numberOfPlayers];
		
		int cursor = 5; //set the cursor to the opening parenthesis of the first power.
		for(int pow=0; pow<this.numberOfPlayers; pow++){
						
			powers[pow] = smrMessage[cursor + 1];
			names[pow] = smrMessage[cursor + 3];
			numSCs[pow] = Integer.parseInt(smrMessage[cursor + 8]);
			if(numSCs[pow] == 0){
				yearOfElimination[pow] = Integer.parseInt(smrMessage[cursor + 9]);
				cursor += 11; //set the cursor to the opening parenthesis of the next power.
			}else{
				yearOfElimination[pow] = 0;
				cursor += 10; //set the cursor to the opening parenthesis of the next power.
			}
			
			if(numSCs[pow] >= 18){
				endedInSolo = true;
				numSurvivors = 1;
			}
			
			/*
			String nameWithoutQuotes = names[pow].replace("'", "");
			if(markedPlayers.contains(powers[pow]) || markedPlayers.contains(nameWithoutQuotes)){
				isMarked[pow] = true;
			}*/

		}
		
		//to determine the player results we need to use another for loop, because we have to know if there is a solo victory beforehand.
		for(int pow=0; pow<this.numberOfPlayers; pow++){
			
			
			if(numSCs[pow] == 0){
				playerResults[pow] = PlayerResult.ELIMINATED;
			
			}else if(numSCs[pow] >= 18){
				playerResults[pow] = PlayerResult.SOLO;
			
			}else if(endedInSolo){
				playerResults[pow] = PlayerResult.LOST; //the game ended in a solo, but the current power is not the winner.
			
			}else{
				playerResults[pow] = PlayerResult.DRAW; //the game ended in a draw, and the current power is not eliminated.
				numSurvivors++;
			
			}
			
		}
		
		rankPlayers();
			
	}
	
	/**
	 * Orders the players, from winners to losers.
	 * 
	 */
	private void rankPlayers(){
		
		rank2playerNumber = new int[this.numberOfPlayers]; //note: the player who ends first will have index 0 in this array.
		
		boolean[] hasRank = new boolean[this.numberOfPlayers];
		int numRankedPlayers = 0;
		int i = -1;
		int bestPlayer = -1;
		
		//we complete a number of cycles. In every cycle we loop over each player that hasn't been ranked yet,
		//the best one of those will receive the new rank.
		while(numRankedPlayers < this.numberOfPlayers){
			
			i = (i+1) % this.numberOfPlayers; //go to next player.
			
			//after completing a full cycle we can add the best player of the previous cycle.
			if(i==0 && bestPlayer != -1){
				
				rank2playerNumber[numRankedPlayers] = bestPlayer;
				numRankedPlayers++;
				hasRank[bestPlayer] = true;
				
				bestPlayer = -1;
			}
			
			//if player i already has a rank, continue.
			if(hasRank[i]){
				continue;
			}
			
			if(bestPlayer == -1){	//if i is the first player in this cycle, it is set as best player.
				bestPlayer = i; 
			}else if(compare(i, bestPlayer) > 0){ //otherwise, compare i with the player that was the best so far this cycle.
				bestPlayer = i;
			}
			
		}
		
		
		
		for(int j=0; j<this.numberOfPlayers; j++){
			
			//for the player ranked j, determine how many players have finished equally.
			
			int player1 = rank2playerNumber[j];
			
			int lowestRank = j;
			int highestRank = j;
			for(int k=j+1; k<this.numberOfPlayers; k++){
				
				int player2 = rank2playerNumber[k];
				
				if(compare(player1, player2) == 0){
					highestRank = k;
				}else{
					break;
				}
			}
			
			double preciseRank = (((double)highestRank) + ((double)lowestRank)) / 2.0;
			preciseRank += 1.0; //add 1 to take into account that the index in the array is 1 lower than the rank.
		
			//now make sure that all players ranked between j and highest receive this precise rank.
			for(int r = lowestRank; r <= highestRank; r++){
				
				int player = rank2playerNumber[r];
				
				playerNumber2preciseRank[player] = preciseRank;
			}
			
			j=highestRank;
		}
	}
	
	/**
	 * Returns the index of the player with the given name.
	 * Returns -1 if the name doesn't exist.
	 * @param name
	 * @return
	 */
	int getIndexOf(String name){
		for(int i=0; i<names.length; i++){
			/*if(names[i].equals("'" + name + "'")){
				return i;
			}*/
			if(names[i].equals(name)){
				return i;
			}
		}
		return -1;
	}
	
	boolean containsName(String name){
		return getIndexOf(name) != -1;
	}
	
	/**
	 * Returns a list with the names of all the players that participated in this game.
	 * @return
	 */
	public ArrayList<String> getNames(){
		
		ArrayList<String> _names = new ArrayList<String>();
		for(String s : this.names){
			_names.add(s);
		}
		
		return _names;
	}
	
	/**
	 * Returns true if this game ended in a solo victory.
	 * @return
	 */
	public boolean endedInSolo(){
		return endedInSolo;
	}
	
	/**
	 * Returns the number of players that did not get eliminated. 
	 * That is: the number of players that ended the game with at least 1 unit.
	 * 
	 */
	public int getNumSurvivors() {
		return numSurvivors;
	}

	/**
	 * Returns the rank in this game of the player with the given name.
	 * e.g. if a player with name DumbBot_1 finished in 5th place then calling getRank("DumbBot_1") will return 5.
	 * 
	 * If DumbBot_1 and another player together finished in a shared 5 place, then calling getRank("DumbBot_1") will return 5.5.
	 * 
	 * @param name
	 * @return
	 */
	public double getRank(String name){
		
		int playerIndex = getIndexOf(name);
		
		if(playerIndex == -1){
			throw new RuntimeException("GameResult.getRank() Error! This game did not involve any player with name " + name);
		}
		
		return playerNumber2preciseRank[playerIndex];
	}
	
	/**
	 * Returns the number of supply centers at the end of the game of the player with the given name.
	 * @param name
	 * @return
	 */
	public int getNumSupplyCenters(String name){
		
		int playerIndex = getIndexOf(name);
		
		if(playerIndex == -1){
			throw new RuntimeException("GameResult.getNumSupplyCenters() Error! This game did not involve any player with name " + name);
		}
		
		return numSCs[playerIndex];
	}
	

	
	/**
	 * If the player with the given name got eliminated this method returns the year in which it was eliminated.
	 * If the player was not eliminated it returns 0.
	 * @param name
	 * @return
	 */
	public int getYearOfElimination(String name){
		
		int playerIndex = getIndexOf(name);
		
		if(playerIndex == -1){
			throw new RuntimeException("GameResult.getYearOfElimination() Error! This game did not involve any player with name " + name);
		}
		
		return yearOfElimination[playerIndex];
	}
	
	/**
	 * Returns the power played by the player with the given name.
	 * @param playerName
	 * @return
	 */
	public String getPowerPlayed(String playerName){
		
		int playerIndex = getIndexOf(playerName);
		
		if(playerIndex == -1){
			throw new RuntimeException("GameResult.getPowerPlayed() Error! This game did not involve any player with name " + playerName);
		}
		
		return powers[playerIndex];
	}
	
	/**
	 * Returns the name of the player that played the given power.
	 * 
	 * @param powerName must be one of the following: "AUS", "ENG", "FRA", "GER", "ITA", "RUS" or "TUR".
	 * @return
	 */
	public String getPlayerNameByPower(String powerName){
		
		int index;
		for(index=0; index<powers.length; index++){
			if(powers[index].equals(powerName)){
				return names[index];
			}
		}
		
		throw new RuntimeException("GameResult.getPlayerNameByPower() Error! the given powerName " + powerName + " is incorrect. Please provide one of the following power names: " + Arrays.toString(powers));
	}
	
	/**
	 * Returns the name of the player that obtained a Solo Victory, or returns null if the game ended in a draw.
	 * @return
	 */
	public String getSoloWinner(){
		
		if(!endedInSolo){
			return null;
		}
		
		for(int i=0; i<this.numberOfPlayers; i++){
			
			if(numSCs[i] >= 18){
				return names[i];
			}
		}
		
		throw new RuntimeException("GameResult.getSoloWinner() Error! Result is solo victory, but no player has 18 or more supply centers.");
	}
	
	@Override
	public String toString(){
		
		//Make sure the players are ranked.
		if(rank2playerNumber == null){
			rankPlayers();
		}
		
		String string = "";
		
		for(int j=0; j<this.numberOfPlayers; j++){
			int playerIndex = rank2playerNumber[j];
			
			string += "" + (j+1)+ ". " + names[playerIndex] + " " + powers[playerIndex]; 
			
			/*
			if(isMarked[playerIndex]){
				string += "*";
			}*/
			string += " ";
			
			if(numSCs[playerIndex] > 0){
				string += numSCs[playerIndex];
			}else{
				string += yearOfElimination[playerIndex];
			}
			
			string += "\n";
		}
		
		return string;
	}
	
	/**
	 * Returns positive number if player1 scores better than player2.
	 * Returns negative number if player2 scores better than player1.
	 * Returns 0 if they score equal.
	 * 
	 * @param player1
	 * @param player2
	 * @return
	 */
	int compare(int player1, int player2){
		
		if(numSCs[player1] == 0 && numSCs[player2] == 0){
			return yearOfElimination[player1] - yearOfElimination[player2];
		}
		
		return numSCs[player1] - numSCs[player2];
	}
	
}
