package ddejonge.bandana.tournament;

import java.util.HashMap;

public abstract class ScoreCalculator {

	boolean higherIsBetter;
	
	private HashMap<String, Integer> names2numGamesPlayed = new HashMap<String, Integer>();
	private HashMap<String, Double> names2totalScore = new HashMap<String, Double>();
	
	/**
	 * 
	 * @param higherIsBetter if this parameter is true, then the player that scores the highest value is ranked highest. 
	 * If this parameter is false, then the player that scores the lowest value will be ranked highest.
	 * 
	 */
	public ScoreCalculator(boolean higherIsBetter){
		this.higherIsBetter = higherIsBetter;
	}
	
	/**
	 * This method is called after every finished game. 
	 * It will get the score for each player by calling calculateGameScore() and adds this score to that player's total.
	 * 
	 * 
	 * 
	 * @param newResult
	 */
	void addResult(GameResult newResult){
		
		for(String playerName : newResult.getNames()){
			
			increaseNumberOfGamesPlayed(playerName);
			
			double score = calculateGameScore(newResult, playerName);
			
			addScoreToTotal(playerName, score);
			
		}
	}
	
	protected void increaseNumberOfGamesPlayed(String playerName){
		
		//get the old value from the table
		Integer numGamesPlayed = getNumberOfGamesPlayed(playerName);
		
		//increment the value.
		numGamesPlayed++;
		
		//store the new value in the table.
		names2numGamesPlayed.put(playerName, numGamesPlayed);
	}
	
	private void addScoreToTotal(String playerName, double score){
		
		//get the old value from the table
		Double totalScore = getTotalScore(playerName);
		
		//increment the value.
		totalScore += score;
		
		//store the new value in the table.
		names2totalScore.put(playerName, totalScore);
	}
	
	

	
	public int getNumberOfGamesPlayed(String playerName){
		
		Integer numGamesPlayed = names2numGamesPlayed.get(playerName);

		//if it wasn't in the table then set it to 0
		if(numGamesPlayed == null){
			return 0;
		}
		
		return numGamesPlayed;
	}
	
	public double getTotalScore(String playerName){
		
		//get the old value from the table
		Double totalScore = names2totalScore.get(playerName);
		
		//if it wasn't in the table then return 0.0
		if(totalScore == null){
			totalScore = 0.0;
		}
		
		return totalScore;
	}
	
	public double getAverageScore(String playerName){
		
		double totalScore = getTotalScore(playerName);
		int numGamesPlayed = getNumberOfGamesPlayed(playerName);
		if(numGamesPlayed == 0){
			return 0;
		}
		
		return totalScore / (double)numGamesPlayed;
		
	}
	
	/**
	 * Calculates the score of the given player for the given game.
	 * @param newResult
	 * @param name
	 * @return
	 */
	public abstract double calculateGameScore(GameResult newResult, String playerName);
	
	/**
	 * Returns the overall score of the given player for the entire tournament. <br/>
	 * The TournamentObserver will sorts the players based on to the values returned by this method.
	 * @param name
	 * @return
	 */
	public abstract double getTournamentScore(String playerName);
	
	/**
	 * Returns the name of this score system.
	 * @return
	 */
	public abstract String getScoreSystemName();
	
	/**
	 * Returns the string to display in the table of the TournamentObserver.
	 * @param name
	 * @return
	 */
	public abstract String getScoreString(String playerName);
}
