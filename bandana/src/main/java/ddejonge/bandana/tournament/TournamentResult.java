package ddejonge.bandana.tournament;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;


public class TournamentResult {
	

	public ArrayList<GameResult> gameResults = new ArrayList<GameResult>();
	
	ArrayList<ScoreCalculator> scoreCalculators = new ArrayList<ScoreCalculator>();
	
	ArrayList<String> names;
	
	int[] numGamesPlayed;


	
	public TournamentResult(int numParticipants, ArrayList<ScoreCalculator> scoreCalculators){
		
		names = new ArrayList<String>(numParticipants);
		
		numGamesPlayed = new int[numParticipants];
		
		this.scoreCalculators = scoreCalculators;
	}
	
	public void addResult(GameResult newResult){
		
		this.gameResults.add(newResult);
		
		for(ScoreCalculator scoreCalculator : scoreCalculators){
			scoreCalculator.addResult(newResult);
		}
		
		for(String name : newResult.getNames()){
			if( ! names.contains(name)){
				this.names.add(name);
			}
		}
		
		
		for(String name : names){
			
			int index = getIndex(name);
			
			if(newResult.containsName(name)){
				numGamesPlayed[index]++;
			}
			
		}
	}
	
	int getIndex(String name){
		for(int i=0; i<names.size(); i++){
			if(names.get(i).equals(name)){
				return i;
			}
		}
		
		throw new RuntimeException("TournamentResult.getIndex() Player with name " + name + " is unknown.");
	}
	
	
	public ArrayList<String> getNames() {
		return names;
	}
	
	public String toString(){
		
		ArrayList<String> sortedNames = sortNames(this.scoreCalculators);
		
		String s = "";
		for(String name : sortedNames){
			
			int index = getIndex(name);
			
			int played = numGamesPlayed[index];
			
			s += name + ": " + System.lineSeparator();
			s += "games played: " + played + System.lineSeparator();
			
			for(ScoreCalculator scoreCalculator : scoreCalculators){
				
				
				s += scoreCalculator.getScoreSystemName() + ": " + scoreCalculator.getScoreString(name) + System.lineSeparator();
				
				
				/*
				double totalScore = scoreCalculator.getScore(name);
				
				//round it off to 3 digits:
				totalScore = Utilities.round(totalScore, 3);
				
				//calculate the average:
				double averageScore = totalScore/((double)played);
				
				//round it off to 3 digits:
				averageScore = Utilities.round(averageScore, 3);
				
				
				s += scoreCalculator.getScoreSystemName() + ": " + totalScore + " (" + averageScore + ")" + System.lineSeparator();
				*/
			}
			s += System.lineSeparator();
		}
		
		
		return s;
	}
	
	public ArrayList<String> sortNames(ArrayList<ScoreCalculator> scoreCalculators){
		
		ArrayList<String> sortedNames = new ArrayList<String>(names);
		
		Collections.sort(sortedNames, new Comparator<String>() {
			
			@Override
			public int compare(String player1, String player2) {

				for(ScoreCalculator scoreCalculator : scoreCalculators){
					
					double score1 = scoreCalculator.getTournamentScore(player1);
					double score2 = scoreCalculator.getTournamentScore(player2);
					
					if(Math.abs(score1 - score2) < 0.0001){
						continue;
					}
					
					if(scoreCalculator.higherIsBetter){
						
						if(score1 < score2){
							return 1;
						}else{
							return -1;
						}
						
					}else{
						
						if(score1 > score2){
							return 1;
						}else{
							return -1;
						}
					}
					
				}
				
				return 0;
			}});
		
		
		return sortedNames;
		
	}
	
	/*
	public ArrayList<String> sortNames(ArrayList<ScoringSystem> scoringSystems){
		
		ArrayList<String> sortedNames = new ArrayList<String>(names);
		
		Collections.sort(sortedNames, new Comparator<String>() {

			@Override
			public int compare(String name1, String name2) {
				float score1;
				float score2;
				
				for(int i=0; i<scoringSystems.size(); i++){
					
					ScoringSystem scoringSystem = scoringSystems.get(i);
					
					score1 = getScore(name1, scoringSystem);
					score2 = getScore(name2, scoringSystem);
					
					if(scoringSystem == ScoringSystem.RANK){
						
						//For RANK we have: the lower the better.
						if(score1 > score2){
							return 1;
						}
						if(score1 < score2){
							return -1;
						}
						
					}else{
						
						//For other scoring systems we have: the higher the better.
						
						if(score1 < score2){
							return 1;
						}
						if(score1 > score2){
							return -1;
						}
					}
				}
				
				return 0;
			}
		});
		
		
		return sortedNames;
		
	}
	*/
	
}
