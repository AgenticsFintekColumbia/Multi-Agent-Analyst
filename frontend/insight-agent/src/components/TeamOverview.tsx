import { Building2, Users, UserCog, BarChart3, TrendingUp, Newspaper } from "lucide-react";
import { Card } from "@/components/ui/card";
import { AppMode } from "@/pages/Index";

interface TeamOverviewProps {
  mode: Exclude<AppMode, null>;
}

const agentIcons = {
  Manager: UserCog,
  "Fundamental Analyst": BarChart3,
  "Technical Analyst": TrendingUp,
  "News & Sentiment Analyst": Newspaper,
};

export const TeamOverview = ({ mode }: TeamOverviewProps) => {
  const isExplainer = mode === "explainer";
  const teamName = isExplainer ? "Explainer Team" : "Recommender Team";
  const subtitle = isExplainer 
    ? "Q1 · Explain Human Analyst Rating" 
    : "Q2 · Model Buy / Hold / Sell Rating";
  const description = isExplainer
    ? "A specialized team that analyzes and explains why human analysts gave their stock ratings by examining fundamental data, technical indicators, and news sentiment."
    : "An independent team that generates model-driven stock recommendations by synthesizing insights from fundamental, technical, and sentiment analysis.";
  
  return (
    <Card className={`p-8 mb-8 relative overflow-hidden border border-border/50 bg-card/50 backdrop-blur-sm ${
      isExplainer 
        ? "border-explainer/20" 
        : "border-recommender/20"
    }`}>
      <div className={`absolute top-0 right-0 w-48 h-48 rounded-full blur-3xl opacity-20 ${
        isExplainer ? "bg-explainer" : "bg-recommender"
      }`} />
      <div className="relative space-y-6">
        <div>
          <h2 className="text-3xl font-black mb-2 text-foreground tracking-tight">
            {teamName}
          </h2>
          <p className="text-sm font-semibold text-muted-foreground mb-3 tracking-wide">
            {subtitle}
          </p>
          <p className="text-sm text-foreground/70 leading-relaxed max-w-3xl">
            {description}
          </p>
        </div>
        
        <div className="pt-4 border-t border-border/50">
          <div className="flex items-center gap-2 mb-4">
            <Users className={`w-4 h-4 ${isExplainer ? "text-explainer" : "text-recommender"}`} />
            <span className="text-xs font-semibold text-foreground/80 uppercase tracking-wider">Active Agents</span>
          </div>
          <div className="flex items-center gap-2.5 flex-wrap">
            {["Manager", "Fundamental Analyst", "Technical Analyst", "News & Sentiment Analyst"].map((agent) => {
              const Icon = agentIcons[agent as keyof typeof agentIcons];
              return (
                <span 
                  key={agent}
                  className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-full text-xs font-semibold border transition-all duration-300 hover:scale-105 ${
                    isExplainer 
                      ? "bg-explainer/10 text-explainer border-explainer/30 hover:bg-explainer/20 hover:border-explainer/50" 
                      : "bg-recommender/10 text-recommender border-recommender/30 hover:bg-recommender/20 hover:border-recommender/50"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {agent}
                </span>
              );
            })}
          </div>
        </div>
      </div>
    </Card>
  );
};
