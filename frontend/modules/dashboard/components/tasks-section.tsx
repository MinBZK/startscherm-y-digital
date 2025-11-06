import { getTasksData } from "@/modules/dashboard/actions/tasks-server-util";
import { Task } from "@/lib/types";
import { SectionCard } from "./card-section";
import { TaskItem } from "./task-item";

export async function TasksSection() {
  const tasks = await getTasksData();
  return (
    <SectionCard
      title="Mijn taken"
      buttonLabel="Alle taken"
      buttonAction="Alle taken"
    >
      {tasks.map((task: Task, idx: number) => (
        <TaskItem
          key={task.id}
          task={task}
          bordered={idx !== tasks.length - 1}
        />
      ))}
    </SectionCard>
  );
}
