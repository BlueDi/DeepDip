package ddejonge.bandana.tournament;


import ddejonge.negoServer.Utils;

public class RankCalculator extends ScoreCalculator{

	
	
	public RankCalculator() {
		super(false); //We have to pass 'false' to the super constructor to make sure that players with LOWER rank are ranked HIGHER in the tournament result.
	}

	@Override
	public double calculateGameScore(GameResult newResult, String playerName){
		return newResult.getRank(playerName); //the rank is already calculated by the GameResult object, so we just need to return it.
	}

	@Override
	public double getTournamentScore(String playerName) {
		return  this.getAverageScore(playerName);
	}



	@Override
	public String getScoreSystemName() {
		return "Average Rank";
	}

	@Override
	public String getScoreString(String playerName) {
		
		double roundedScore = Utils.round(this.getTournamentScore(playerName), 3);
		
		return "" + roundedScore;
	}
}
