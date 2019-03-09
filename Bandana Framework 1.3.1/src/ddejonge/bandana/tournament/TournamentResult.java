package ddejonge.bandana.tournament;

import java.util.ArrayList;


public class TournamentResult {
    public ArrayList<GameResult> gameResults = new ArrayList<>();
    private ArrayList<ScoreCalculator> scoreCalculators;
    private ArrayList<String> names;
    private int[] numGamesPlayed;


    TournamentResult(int numParticipants, ArrayList<ScoreCalculator> scoreCalculators) {

        names = new ArrayList<>(numParticipants);

        numGamesPlayed = new int[numParticipants];

        this.scoreCalculators = scoreCalculators;
    }

    void addResult(GameResult newResult) {

        this.gameResults.add(newResult);

        for (ScoreCalculator scoreCalculator : scoreCalculators) {
            scoreCalculator.addResult(newResult);
        }

        for (String name : newResult.getNames()) {
            if (!names.contains(name)) {
                this.names.add(name);
            }
        }

        for (String name : names) {
            int index = getIndex(name);
            if (newResult.containsName(name)) {
                numGamesPlayed[index]++;
            }
        }
    }

    private int getIndex(String name) {
        for (int i = 0; i < names.size(); i++) {
            if (names.get(i).equals(name)) {
                return i;
            }
        }

        throw new RuntimeException("TournamentResult.getIndex() Player with name " + name + " is unknown.");
    }

    public ArrayList<String> getNames() {
        return names;
    }

    public String toString() {
        ArrayList<String> sortedNames = sortNames(this.scoreCalculators);
        StringBuilder s = new StringBuilder();
        for (String name : sortedNames) {
            int index = getIndex(name);
            int played = numGamesPlayed[index];

            s.append(name).append(": ").append(System.lineSeparator());
            s.append("games played: ").append(played).append(System.lineSeparator());

            for (ScoreCalculator scoreCalculator : scoreCalculators) {
                s.append(scoreCalculator.getScoreSystemName()).append(": ").append(scoreCalculator.getScoreString(name)).append(System.lineSeparator());
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
            s.append(System.lineSeparator());
        }
        return s.toString();
    }

    public ArrayList<String> sortNames(ArrayList<ScoreCalculator> scoreCalculators) {
        ArrayList<String> sortedNames = new ArrayList<>(names);
        sortedNames.sort((player1, player2) -> {
            for (ScoreCalculator scoreCalculator : scoreCalculators) {
                double score1 = scoreCalculator.getTournamentScore(player1);
                double score2 = scoreCalculator.getTournamentScore(player2);

                if (Math.abs(score1 - score2) < 0.0001) {
                    continue;
                }

                if (scoreCalculator.higherIsBetter) {
                    if (score1 < score2) {
                        return 1;
                    } else {
                        return -1;
                    }
                } else {
                    if (score1 > score2) {
                        return 1;
                    } else {
                        return -1;
                    }
                }
            }
            return 0;
        });
        return sortedNames;
    }
}
