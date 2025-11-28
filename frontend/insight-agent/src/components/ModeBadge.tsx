import { Search, TrendingUp } from "lucide-react";
import { AppMode } from "@/pages/Index";

interface ModeBadgeProps {
  mode: Exclude<AppMode, null>;
}

export const ModeBadge = ({ mode }: ModeBadgeProps) => {
  const isExplainer = mode === "explainer";
  
  return (
    <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${
      isExplainer 
        ? "bg-explainer/10 text-explainer border border-explainer/20" 
        : "bg-recommender/10 text-recommender border border-recommender/20"
    }`}>
      {isExplainer ? <Search className="w-4 h-4" /> : <TrendingUp className="w-4 h-4" />}
      <span className="font-semibold text-sm">
        {isExplainer ? "Explainer" : "Recommender"}:
      </span>
      <span className="text-sm">
        {isExplainer ? "Explain analyst rating" : "Model's own rating"}
      </span>
    </div>
  );
};
