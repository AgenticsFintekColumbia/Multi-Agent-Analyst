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
      <header className="text-center mb-20 animate-in fade-in duration-700">
        <div className="inline-block mb-6">
          <div className="px-4 py-2 rounded-full bg-gradient-to-r from-primary/10 to-success/10 border border-primary/20 inline-flex items-center gap-2 mb-6">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            <span className="text-xs font-mono font-semibold text-primary uppercase tracking-wider">AI-Powered Analysis</span>
          </div>
        </div>
        <h1 className="text-6xl md:text-7xl font-black mb-6 bg-gradient-to-r from-foreground via-primary to-success bg-clip-text text-transparent leading-tight">
          Agentic Recommendation
          <br />
          <span className="bg-gradient-to-r from-primary via-success to-primary bg-clip-text text-transparent animate-pulse-slow">
            System
          </span>
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed font-light">
          Multi-agent AI system powered by <span className="font-semibold text-foreground">Google Gemini</span> and <span className="font-semibold text-foreground">CrewAI</span> to analyze and generate stock analyst recommendations
        </p>
        <div className="mt-8 flex items-center justify-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
            <span className="font-mono">Real-time Analysis</span>
          </div>
          <div className="w-1 h-1 rounded-full bg-border" />
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse delay-500" />
            <span className="font-mono">Multi-Agent AI</span>
          </div>
        </div>
      </header>

      <div className="grid md:grid-cols-2 gap-8 mb-12">
        <Card 
          className="group relative overflow-hidden transition-all duration-500 hover:shadow-2xl hover:-translate-y-2 cursor-pointer border-2 border-explainer/20 hover:border-explainer/50 bg-gradient-to-br from-card to-card/50"
          onClick={() => onSelectMode("explainer")}
        >
          <div className="absolute inset-0 bg-gradient-to-br from-explainer/10 via-explainer/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="absolute top-0 right-0 w-64 h-64 rounded-full blur-3xl bg-explainer/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          
          <div className="relative p-10">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-explainer to-explainer/80 flex items-center justify-center mb-8 group-hover:scale-110 group-hover:rotate-3 transition-all duration-500 shadow-lg">
              <Search className="w-10 h-10 text-white" />
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
          className="group relative overflow-hidden transition-all duration-500 hover:shadow-2xl hover:-translate-y-2 cursor-pointer border-2 border-recommender/20 hover:border-recommender/50 bg-gradient-to-br from-card to-card/50"
          onClick={() => onSelectMode("recommender")}
        >
          <div className="absolute inset-0 bg-gradient-to-br from-recommender/10 via-recommender/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="absolute top-0 right-0 w-64 h-64 rounded-full blur-3xl bg-recommender/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          
          <div className="relative p-10">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-recommender to-recommender/80 flex items-center justify-center mb-8 group-hover:scale-110 group-hover:rotate-3 transition-all duration-500 shadow-lg">
              <TrendingUp className="w-10 h-10 text-white" />
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

      <Card className="p-8 bg-gradient-to-br from-muted/40 to-muted/20 border-2 border-border/50 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-primary/5 to-transparent animate-shimmer" />
        <div className="relative">
          <p className="text-center text-base text-foreground/80 leading-relaxed font-medium">
            Once you choose a mode, you'll be able to pick a ticker, a specific IBES recommendation, and generate the output.
          </p>
        </div>
      </Card>
    </div>
  );
};
