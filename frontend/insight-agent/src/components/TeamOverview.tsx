import { Building2, Users } from "lucide-react";
import { Card } from "@/components/ui/card";
import { AppMode } from "@/pages/Index";

interface TeamOverviewProps {
  mode: Exclude<AppMode, null>;
}

export const TeamOverview = ({ mode }: TeamOverviewProps) => {
  const isExplainer = mode === "explainer";
  
  return (
    <Card className={`p-8 mb-8 relative overflow-hidden border-2 ${
      isExplainer 
        ? "bg-gradient-to-br from-explainer/15 via-explainer/8 to-explainer/5 border-explainer/30" 
        : "bg-gradient-to-br from-recommender/15 via-recommender/8 to-recommender/5 border-recommender/30"
    }`}>
      <div className={`absolute top-0 right-0 w-48 h-48 rounded-full blur-3xl opacity-30 ${
        isExplainer ? "bg-explainer" : "bg-recommender"
      }`} />
      <div className="relative">
        <div className="flex items-start gap-5 mb-6">
          <div className={`w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg ${
            isExplainer 
              ? "bg-gradient-to-br from-explainer to-explainer/80 text-white" 
              : "bg-gradient-to-br from-recommender to-recommender/80 text-white"
          }`}>
            <Building2 className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-3xl font-black mb-2 bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              {isExplainer ? "🔍 Explainer Team" : "📊 Recommender Team"}
            </h2>
            <p className="text-sm font-mono text-muted-foreground uppercase tracking-wider">
              {isExplainer 
                ? "Q1 · Explain human analyst rating" 
                : "Q2 · Model buy / hold / sell rating"}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-3 flex-wrap">
          <Users className={`w-5 h-5 ${isExplainer ? "text-explainer" : "text-recommender"}`} />
          <span className="text-sm font-bold text-foreground/80">Active Agents:</span>
          {["Manager", "Fundamental Analyst", "Technical Analyst", "News & Sentiment Analyst"].map((agent, idx) => (
            <span 
              key={agent}
              className={`px-4 py-2 rounded-xl text-xs font-bold border-2 transition-all duration-300 hover:scale-105 ${
                isExplainer 
                  ? "bg-explainer/10 text-explainer border-explainer/30 hover:bg-explainer/20" 
                  : "bg-recommender/10 text-recommender border-recommender/30 hover:bg-recommender/20"
              }`}
            >
              {idx + 1}. {agent}
            </span>
          ))}
        </div>
      </div>
    </Card>
  );
};
