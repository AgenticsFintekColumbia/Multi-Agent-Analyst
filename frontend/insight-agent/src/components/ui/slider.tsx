import * as React from "react";
import * as SliderPrimitive from "@radix-ui/react-slider";

import { cn } from "@/lib/utils";

const Slider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root> & {
    accentColor?: "primary" | "success" | "explainer" | "recommender";
  }
>(({ className, accentColor = "primary", ...props }, ref) => {
  const rangeClasses = {
    primary: "bg-primary",
    success: "bg-success",
    explainer: "bg-explainer",
    recommender: "bg-recommender",
  };

  const thumbClasses = {
    primary: "border-primary",
    success: "border-success",
    explainer: "border-explainer",
    recommender: "border-recommender",
  };

  return (
    <SliderPrimitive.Root
      ref={ref}
      className={cn("relative flex w-full touch-none select-none items-center", className)}
      {...props}
    >
      <SliderPrimitive.Track className="relative h-2.5 w-full grow overflow-hidden rounded-full bg-secondary/50">
        <SliderPrimitive.Range 
          className={cn("absolute h-full transition-colors", rangeClasses[accentColor])} 
        />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb 
        className={cn(
          "block h-5 w-5 rounded-full border-2 bg-background ring-offset-background transition-all duration-300 hover:scale-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
          thumbClasses[accentColor]
        )} 
      />
    </SliderPrimitive.Root>
  );
});
Slider.displayName = SliderPrimitive.Root.displayName;

export { Slider };
