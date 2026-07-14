export interface LessonRequest { description: string }
export interface LessonPlan { title: string; learning_objectives: string[]; duration_minutes: number; sequence: string[] }
export interface ActivityGuide { title: string; materials: string[]; instructions: string[] }
export interface RubricCriterion { criterion: string; achieved: string; developing: string; beginning: string }
export interface Assessment { title: string; instructions: string[]; rubric: RubricCriterion[] }
export interface TeachingPack { lesson_plan: LessonPlan; activities: ActivityGuide; assessment: Assessment; review_notes: string[] }

