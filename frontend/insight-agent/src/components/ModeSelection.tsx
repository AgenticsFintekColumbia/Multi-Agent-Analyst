import { Search, TrendingUp } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AppMode } from "@/pages/Index";

interface ModeSelectionProps {
  onSelectMode: (mode: AppMode) => void;
}

export const ModeSelection = ({ onSelectMode }: ModeSelectionProps) => {
  return (
    <div className="container mx-auto px-4 py-16 max-w-6xl">
      <header className="text-center mb-20">
        <h1 className="text-5xl md:text-6xl font-black mb-4 bg-gradient-to-r from-foreground via-primary to-foreground bg-clip-text text-transparent leading-tight">
          Agentic Recommendation System
        </h1>
        <p className="text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed mb-6">
          A multi-agent AI engine using Google Gemini and CrewAI to generate and justify stock recommendations.
        </p>
        <div className="flex items-center justify-center gap-3 flex-wrap mt-6">
          <span className="px-4 py-1.5 rounded-full bg-primary/10 border border-primary/30 text-primary text-xs font-semibold tracking-wide">
            Real-Time Analysis
          </span>
          <span className="px-4 py-1.5 rounded-full bg-success/10 border border-success/30 text-success text-xs font-semibold tracking-wide">
            Multi-Agent AI
          </span>
          <span className="px-4 py-1.5 rounded-full bg-accent/10 border border-accent/30 text-accent text-xs font-semibold tracking-wide">
            Data-Driven Signals
          </span>
        </div>
      </header>

      <div className="grid md:grid-cols-2 gap-8 mb-12">
        <Card 
          className="group relative overflow-hidden transition-all duration-300 cursor-pointer border-2 border-explainer/30 hover:border-explainer/60 glass-chrome hover:shadow-2xl hover:-translate-y-[6px] hover:shadow-explainer/20"
          onClick={() => onSelectMode("explainer")}
        >
          <div className="absolute inset-0 bg-gradient-to-br from-explainer/10 via-explainer/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="absolute top-0 right-0 w-64 h-64 rounded-full blur-3xl bg-explainer/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="absolute inset-0 ring-2 ring-explainer/0 group-hover:ring-explainer/30 rounded-lg transition-all duration-300" />
          
          <div className="relative p-10">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-explainer to-explainer/80 flex items-center justify-center mb-8 group-hover:scale-105 transition-transform duration-300 shadow-lg">
              <Search className="w-10 h-10 text-white transition-transform duration-300 group-hover:scale-105" />
            </div>
            
            <h2 className="text-4xl font-black mb-4 bg-gradient-to-r from-foreground to-explainer bg-clip-text text-transparent">
              Explainer
            </h2>
            <p className="text-muted-foreground mb-8 leading-relaxed text-base">
              Justify the human analyst's rating based on IBES, FUND, and NEWS context.
            </p>
            
            <ul className="space-y-4 mb-10">
              <li className="flex items-start gap-3 text-sm">
                <div className="w-6 h-6 rounded-lg bg-explainer/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-explainer font-bold">✓</span>
                </div>
                <span className="text-foreground/90 leading-relaxed">Decomposes signals from fundamentals, price moves, and headlines</span>
              </li>
              <li className="flex items-start gap-3 text-sm">
                <div className="w-6 h-6 rounded-lg bg-explainer/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-explainer font-bold">✓</span>
                </div>
                <span className="text-foreground/90 leading-relaxed">Focuses on Q1: Explain Analyst Rating</span>
              </li>
            </ul>
            
            <Button 
              className="w-full h-14 bg-gradient-to-r from-explainer to-explainer/80 hover:from-explainer/90 hover:to-explainer/70 text-white font-bold text-lg shadow-lg hover:shadow-xl transition-all duration-300 rounded-xl group"
              size="lg"
            >
              <span className="flex items-center gap-2">
                Use Explainer
                <Search className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </span>
            </Button>
          </div>
        </Card>

        <Card 
          className="group relative overflow-hidden transition-all duration-300 cursor-pointer border-2 border-recommender/30 hover:border-recommender/60 glass-chrome hover:shadow-2xl hover:-translate-y-[6px] hover:shadow-recommender/20"
          onClick={() => onSelectMode("recommender")}
        >
          <div className="absolute inset-0 bg-gradient-to-br from-recommender/10 via-recommender/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="absolute top-0 right-0 w-64 h-64 rounded-full blur-3xl bg-recommender/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="absolute inset-0 ring-2 ring-recommender/0 group-hover:ring-recommender/30 rounded-lg transition-all duration-300" />
          
          <div className="relative p-10">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-recommender to-recommender/80 flex items-center justify-center mb-8 group-hover:scale-105 transition-transform duration-300 shadow-lg">
              <TrendingUp className="w-10 h-10 text-white transition-transform duration-300 group-hover:scale-105" />
            </div>
            
            <h2 className="text-4xl font-black mb-4 bg-gradient-to-r from-foreground to-recommender bg-clip-text text-transparent">
              Recommender
            </h2>
            <p className="text-muted-foreground mb-8 leading-relaxed text-base">
              Issue the model's own recommendation using multi-analyst signals.
            </p>
            
            <ul className="space-y-4 mb-10">
              <li className="flex items-start gap-3 text-sm">
                <div className="w-6 h-6 rounded-lg bg-recommender/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-recommender font-bold">✓</span>
                </div>
                <span className="text-foreground/90 leading-relaxed">Uses price action & news around the rec date</span>
              </li>
              <li className="flex items-start gap-3 text-sm">
                <div className="w-6 h-6 rounded-lg bg-recommender/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-recommender font-bold">✓</span>
                </div>
                <span className="text-foreground/90 leading-relaxed">Focuses on Q2: Model Rating</span>
              </li>
            </ul>
            
            <Button 
              className="w-full h-14 bg-gradient-to-r from-recommender to-recommender/80 hover:from-recommender/90 hover:to-recommender/70 text-white font-bold text-lg shadow-lg hover:shadow-xl transition-all duration-300 rounded-xl group"
              size="lg"
            >
              <span className="flex items-center gap-2">
                Use Recommender
                <TrendingUp className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </span>
            </Button>
          </div>
        </Card>
      </div>

      <Card className="p-8 glass-chrome border-2 border-border/50 relative overflow-hidden">
        <div className="relative">
          <p className="text-center text-base text-foreground/80 leading-relaxed font-medium">
            Once you choose a mode, you'll be able to pick a ticker, a specific IBES recommendation, and generate the output.
          </p>
        </div>
      </Card>
    </div>
  );
};
