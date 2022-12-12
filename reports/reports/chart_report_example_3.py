from reports.reports.base_chart import ReportBaseChart


class Report(ReportBaseChart):
    name = "Chart example report 3 with mock data"
    chart_type = "pie"
    enabled = False

    def data(self):
        return [120, 33, 74, 55, 9]

    def labels(self):
        return ["One", "Two", "three", "Four", "Five"]

    def query(self):
        return []
