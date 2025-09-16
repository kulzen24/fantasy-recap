import React from 'react';
import { YahooLeagueConnection } from './YahooLeagueConnection';

export function LeaguesSetup() {
  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-chat-text-primary-light dark:text-chat-text-primary-dark mb-2">
          Connect Your Leagues
        </h1>
        <p className="text-chat-text-secondary-light dark:text-chat-text-secondary-dark">
          Connect your Yahoo Fantasy leagues to generate AI-powered recaps and analysis.
        </p>
      </div>

      <YahooLeagueConnection />
      
      <div className="mt-4 p-4 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg">
        <h4 className="font-medium text-purple-800 dark:text-purple-200 mb-2">
          🏈 Yahoo Fantasy Sports
        </h4>
        <p className="text-sm text-purple-700 dark:text-purple-300">
          Connect your real Yahoo Fantasy leagues to import team data, standings, and generate personalized recaps.
          Requires Yahoo account authorization.
        </p>
      </div>
    </div>
  );
}
