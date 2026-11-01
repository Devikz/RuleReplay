// Original synthetic hackathon fixture. No dependencies. Input: due-date payment-date.
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

public class LegacyLoan {
    public static void main(String[] args) {
        LocalDate due = LocalDate.parse(args[0]);
        LocalDate paid = LocalDate.parse(args[1]);
        long late = Math.max(0, ChronoUnit.DAYS.between(due, paid));
        // Baseline V1 behavior intentionally remains on five days.
        System.out.println(late > 5 ? 2500 : 0);
    }
}
