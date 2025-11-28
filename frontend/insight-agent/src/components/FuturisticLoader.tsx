import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface FuturisticLoaderProps {
  message?: string;
  mode?: "explainer" | "recommender";
}

export const FuturisticLoader = ({ message, mode = "explainer" }: FuturisticLoaderProps) => {
  const isExplainer = mode === "explainer";
  
  return (
    <div className="relative flex flex-col items-center justify-center p-12">
      {/* Outer rotating ring */}
      <div className={cn(
        "absolute w-32 h-32 border-2 rounded-full animate-spin-slow",
        isExplainer ? "border-explainer/30" : "border-recommender/30"
      )}>
        <div className={cn(
          "absolute top-0 left-1/2 w-1 h-1 rounded-full transform -translate-x-1/2",
          isExplainer ? "bg-explainer" : "bg-recommender"
        )} />
      </div>
      
      {/* Middle ring */}
      <div className={cn(
        "absolute w-24 h-24 border-2 rounded-full animate-spin-slow",
        isExplainer ? "border-explainer/20" : "border-recommender/20"
      )} style={{ animationDirection: 'reverse', animationDuration: '2s' }}>
        <div className={cn(
          "absolute top-1/2 right-0 w-1 h-1 rounded-full transform translate-x-1/2 -translate-y-1/2",
          isExplainer ? "bg-explainer/80" : "bg-recommender/80"
        )} />
      </div>
      
      {/* Inner pulsing core */}
      <div className={cn(
        "relative z-10 w-16 h-16 rounded-full gradient-metallic border-2 flex items-center justify-center animate-pulse-chrome",
        isExplainer ? "border-explainer/40" : "border-recommender/40"
      )}>
        <Sparkles className={cn(
          "w-8 h-8 animate-pulse",
          isExplainer ? "text-explainer" : "text-recommender"
        )} />
      </div>
      
      {/* Scanning line effect */}
      <div className="absolute inset-0 animate-scan opacity-30" />
      
      {message && (
        <div className="mt-8 text-center">
          <p className="text-lg font-semibold text-foreground mb-2">{message}</p>
          <div className="flex items-center justify-center gap-2 mt-4">
            <div className={cn(
              "w-2 h-2 rounded-full animate-pulse",
              isExplainer ? "bg-explainer" : "bg-recommender"
            )} style={{ animationDelay: '0s' }} />
            <div className={cn(
              "w-2 h-2 rounded-full animate-pulse",
              isExplainer ? "bg-explainer" : "bg-recommender"
            )} style={{ animationDelay: '0.2s' }} />
            <div className={cn(
              "w-2 h-2 rounded-full animate-pulse",
              isExplainer ? "bg-explainer" : "bg-recommender"
            )} style={{ animationDelay: '0.4s' }} />
          </div>
        </div>
      )}
    </div>
  );
};

