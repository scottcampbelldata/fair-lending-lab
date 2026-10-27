export const CASE_STUDY = "https://scottcampbell.io/projects/fair-lending-lab/";
export const REPO = "https://github.com/scottcampbelldata/fair-lending-lab";

// Title band and summary aside, as on the scottcampbell.io project pages.
// The h1 text is the page heading the dashboard already had.
export function ReportBand() {
  return (
    <div className="report-band">
      <div className="report-band-inner">
        <div>
          <div className="report-kicker">Statistical study of public mortgage data</div>
          <h1>Testing mortgage denial gaps in Massachusetts HMDA data</h1>
          <p className="report-lead">
            Five preregistered hypotheses tested on CFPB HMDA application
            records, with BH-FDR and Bonferroni corrections for testing them
            as a family. The results read as a screening signal for a fair
            lending review.
          </p>
        </div>
        <dl className="glance" aria-label="Study summary">
          <dt>The question</dt>
          <dd>Do denial rates differ by race and ethnicity for comparable home purchase loans?</dd>
          <dt>The data</dt>
          <dd>The public HMDA loan application register, filtered to first lien conventional owner occupied home purchases.</dd>
          <dt>The read</dt>
          <dd>An association that shows where a review would look next, not a finding of discrimination. <a href={CASE_STUDY}>Read the case study</a>.</dd>
        </dl>
      </div>
    </div>
  );
}
