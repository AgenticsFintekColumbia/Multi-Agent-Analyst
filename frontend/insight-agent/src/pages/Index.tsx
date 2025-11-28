import { useState } from "react";
import { ModeSelection } from "@/components/ModeSelection";
import { AnalysisWorkspace } from "@/components/AnalysisWorkspace";

export type AppMode = "explainer" | "recommender" | null;

const Index = () => {
  const [mode, setMode] = useState<AppMode>(null);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-card/50 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-success/5 rounded-full blur-3xl animate-pulse-slow delay-1000" />
      </div>
      
      <div className="relative z-10">
        {!mode ? (
          <ModeSelection onSelectMode={setMode} />
        ) : (
          <AnalysisWorkspace mode={mode} onBackToModeSelection={() => setMode(null)} />
        )}
      </div>
    </div>
  );
};

export default Index;
