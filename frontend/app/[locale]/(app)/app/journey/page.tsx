import { api } from "@/lib/api/server";
import type { Appointment, Journey } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import { Notice, PageTitle } from "@/components/ui/ClayCard";
import { JourneyView } from "@/components/forms/JourneyView";

export default async function JourneyPage({ params }: { params: Promise<{ locale: string }> }) {
  const { t } = await localeOf(params);
  const [journeys, appointments] = await Promise.all([api<Journey[]>("/me/journey"), api<Appointment[]>("/booking/mine")]);
  return (
    <>
      <PageTitle intro={t("journey.intro")}>{t("journey.title")}</PageTitle>
      {journeys.ok && appointments.ok ? (
        <JourneyView journeys={journeys.data} appointments={appointments.data} />
      ) : (
        <Notice tone="problem">{t("error.unavailable")}</Notice>
      )}
    </>
  );
}
