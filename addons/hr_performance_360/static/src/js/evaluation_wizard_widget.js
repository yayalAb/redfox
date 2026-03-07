/** @odoo-module **/

import {
    Component,
    useState,
    onWillStart,
    onMounted,
    onPatched,
    useEnv,
} from "@odoo/owl"
import { registry } from "@web/core/registry"
import { standardFieldProps } from "@web/views/fields/standard_field_props"
import { useService } from "@web/core/utils/hooks"

export class EvaluationWizardWidget extends Component {
    setup() {
        this.orm = useService("orm")
        this.dialog = useService("dialog")
        this.notification = useService("notification")
        this.action = useService("action")
        this.env = useEnv()
        // Class-level flag for immediate synchronous blocking
        this._isSaving = false
        this.state = useState({
            currentPage: 0,
            questionsPerPage: 5,
            questions: [],
            sections: [],
            allQuestions: [],
            sectionMapping: {},
            allQuestions: [],
            isSaving: false,
        })

        onWillStart(async () => {
            await this.loadQuestions()
        })

        onMounted(async () => {
            // Also load on mount in case data wasn't available earlier
            if (!this.state.questions.length) {
                // Add a small delay to ensure DOM and data are ready
                setTimeout(async () => {
                    await this.loadQuestions()
                }, 100)
            }
        })
    }

    get record() {
        return this.props.record
    }

    get evaluationRecord() {
        // The widget is on question_data field, so this.record should be the evaluation record
        const record = this.record

        if (record && record.model) {
            // Get the parent evaluation record
            return record.model.root || record
        }

        return record
    }

    async loadQuestions() {
        console.log("[EvaluationWizard] Loading questions...")
        console.log("[EvaluationWizard] Record:", this.record)
        console.log(
            "[EvaluationWizard] Evaluation Record:",
            this.evaluationRecord
        )
        console.log(
            "[EvaluationWizard] Evaluation Record data:",
            this.evaluationRecord?.data
        )

        const evaluationRecord = this.evaluationRecord
        let questionLineIds = []
        let questionLines = []

        // Method 1: Load questions from config_id
        if (evaluationRecord && evaluationRecord.data) {
            const evalData = evaluationRecord.data
            const configId = evalData.config_id

            if (configId) {
                const configIdValue = Array.isArray(configId)
                    ? configId[0]
                    : configId
                if (configIdValue) {
                    try {
                        console.log(
                            "[EvaluationWizard] Loading questions from config_id:",
                            configIdValue
                        )
                        const questions = await this.orm.call(
                            "hr.performance.question",
                            "search_read",
                            [[["config_id", "=", configIdValue]]],
                            {
                                fields: [
                                    "name",
                                    "description",
                                    "sequence",
                                    "display_type",
                                ],
                                order: "sequence, id",
                            }
                        )

                        if (questions && questions.length > 0) {
                            console.log(
                                "[EvaluationWizard] Loaded",
                                questions.length,
                                "questions from config"
                            )

                            // Check if we have existing line_ids
                            const lineIds = evalData.line_ids || []
                            let existingLines = []

                            if (
                                lineIds.length > 0 &&
                                typeof lineIds[0] === "number"
                            ) {
                                // Load existing lines
                                existingLines = await this.orm.read(
                                    "hr.performance.evaluation.line",
                                    lineIds,
                                    ["question_id", "rating", "comment"]
                                )
                            }

                            // Create question lines structure - filter out sections and notes, only keep actual questions
                            questionLines = questions
                                .filter(
                                    q =>
                                        q.display_type === "question" ||
                                        !q.display_type
                                )
                                .map((q, idx) => {
                                    const existingLine = existingLines.find(
                                        l =>
                                            l.question_id &&
                                            (l.question_id[0] === q.id ||
                                                l.question_id === q.id)
                                    )
                                    return {
                                        data: {
                                            question_id: [q.id, q.name],
                                            rating: existingLine
                                                ? existingLine.rating || ""
                                                : "",
                                            comment: existingLine
                                                ? existingLine.comment || ""
                                                : "",
                                        },
                                        id: existingLine
                                            ? existingLine.id
                                            : `new_${idx}`,
                                        questionId: q.id,
                                        isNew: !existingLine,
                                        displayType:
                                            q.display_type || "question",
                                    }
                                })

                            // Store sections for display grouping
                            this.state.sections = questions
                                .filter(
                                    q =>
                                        q.display_type === "line_section" ||
                                        q.display_type === "line_note"
                                )
                                .map(s => ({
                                    id: s.id,
                                    name: s.name,
                                    type: s.display_type,
                                    sequence: s.sequence,
                                }))

                            // Store full question list for section grouping
                            this.state.allQuestions = questions
                        }
                    } catch (error) {
                        console.error(
                            "[EvaluationWizard] Error loading from config:",
                            error
                        )
                    }
                }
            }
        }

        // Method 2: If no questions loaded yet, check existing line_ids
        if (
            !questionLines.length &&
            evaluationRecord &&
            evaluationRecord.data
        ) {
            const lineIds = evaluationRecord.data.line_ids
            if (lineIds && Array.isArray(lineIds) && lineIds.length > 0) {
                try {
                    // Load existing evaluation lines
                    const existingLines = await this.orm.read(
                        "hr.performance.evaluation.line",
                        lineIds.filter(id => typeof id === "number"),
                        ["question_id", "rating", "comment"]
                    )

                    // Get question details for these lines
                    const questionIds = existingLines.map(l => l.question_id[0])
                    if (questionIds.length > 0) {
                        const questions = await this.orm.read(
                            "hr.performance.question",
                            questionIds,
                            ["name", "description"]
                        )

                        questionLines = questions.map(q => {
                            const line = existingLines.find(
                                l => l.question_id[0] === q.id
                            )
                            return {
                                data: {
                                    question_id: [q.id, q.name],
                                    rating: line ? line.rating || "" : "",
                                    comment: line ? line.comment || "" : "",
                                },
                                id: line ? line.id : `new_${q.id}`,
                                questionId: q.id,
                                isNew: !line,
                            }
                        })
                    }
                } catch (error) {
                    console.error(
                        "[EvaluationWizard] Error loading existing lines:",
                        error
                    )
                }
            }
        }

        // Process question lines - they already have question data loaded
        if (questionLines.length) {
            this.state.questions = questionLines.map(line => {
                const questionId =
                    line.questionId ||
                    line.data?.question_id?.[0] ||
                    line.data?.question_id
                const questionName = line.data?.question_id?.[1] || ""

                return {
                    id: questionId,
                    question_id: questionId,
                    text: questionName || `Question ${questionId}`,
                    description: line.data?.description || "",
                    lineRecord: line,
                    lineId: line.id,
                    rating: line.data?.rating || "",
                    displayType: line.displayType || "question",
                }
            })

            console.log(
                "[EvaluationWizard] Final questions state:",
                this.state.questions
            )
        } else {
            console.warn("[EvaluationWizard] No questions loaded!")
        }

        // Build section mapping for display
        if (this.state.allQuestions && this.state.allQuestions.length) {
            this.buildSectionMapping()
        }
    }

    get totalPages() {
        if (!this.state.questions || !this.state.questions.length) return 1
        return Math.ceil(
            this.state.questions.length / this.state.questionsPerPage
        )
    }

    buildSectionMapping() {
        // Build mapping of questions to their sections based on sequence
        const sectionMap = {}
        let currentSection = null
        let sectionNumber = 0
        let questionNumberInSection = 0

        // Sort all questions by sequence
        const sortedAll = [...this.state.allQuestions].sort((a, b) => {
            if (a.sequence !== b.sequence) return a.sequence - b.sequence
            return a.id - b.id
        })

        sortedAll.forEach(item => {
            if (item.display_type === "line_section") {
                sectionNumber++
                questionNumberInSection = 0
                currentSection = {
                    id: item.id,
                    name: item.name,
                    type: "section",
                    number: sectionNumber,
                }
            } else if (item.display_type === "line_note") {
                // Notes are also sections but lighter style
                sectionNumber++
                questionNumberInSection = 0
                currentSection = {
                    id: item.id,
                    name: item.name,
                    type: "note",
                    number: sectionNumber,
                }
            } else if (item.display_type === "question" || !item.display_type) {
                questionNumberInSection++
                // This is a question - assign it to current section
                if (!sectionMap[currentSection?.id || "none"]) {
                    sectionMap[currentSection?.id || "none"] = {
                        section: currentSection,
                        questions: [],
                    }
                }
                sectionMap[currentSection?.id || "none"].questions.push({
                    id: item.id,
                    number: questionNumberInSection,
                })
            }
        })

        this.state.sectionMapping = sectionMap
        this.state.sectionNumbers = sectionNumber
    }

    getSectionForQuestion(questionId) {
        if (!this.state.sectionMapping) return null

        for (const [sectionId, data] of Object.entries(
            this.state.sectionMapping
        )) {
            const questionEntry = data.questions.find(q => q.id === questionId)
            if (questionEntry) {
                return {
                    ...data.section,
                    questionNumber: questionEntry.number,
                }
            }
        }
        return null
    }

    get currentQuestions() {
        if (!this.state.questions || !this.state.questions.length) return []
        const start = this.state.currentPage * this.state.questionsPerPage
        const end = start + this.state.questionsPerPage
        return this.state.questions.slice(start, end).map(q => {
            const section = this.getSectionForQuestion(q.question_id)
            return {
                ...q,
                section: section,
                displayNumber: section
                    ? `${section.number}.${section.questionNumber}`
                    : null,
            }
        })
    }

    get isLastPage() {
        return this.state.currentPage === this.totalPages - 1
    }

    get employeeName() {
        const evaluationRecord = this.evaluationRecord
        if (evaluationRecord && evaluationRecord.data) {
            const employeeId = evaluationRecord.data.employee_id
            if (Array.isArray(employeeId) && employeeId.length > 1) {
                return employeeId[1] // Return the employee name
            }
            if (
                employeeId &&
                typeof employeeId === "object" &&
                employeeId.name
            ) {
                return employeeId.name
            }
        }
        // Try to read from the record if available
        if (evaluationRecord && evaluationRecord.resId) {
            // Fallback: try to get from the record directly
            return evaluationRecord.data?.employee_id?.[1] || "Employee"
        }
        return "Employee"
    }

    get evaluationDate() {
        const evaluationRecord = this.evaluationRecord
        if (evaluationRecord && evaluationRecord.data) {
            const date = evaluationRecord.data.evaluation_date
            if (date) {
                // Format date if needed (Odoo usually provides dates in YYYY-MM-DD format)
                const dateObj = new Date(date)
                if (!isNaN(dateObj.getTime())) {
                    return dateObj.toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                    })
                }
                return date
            }
        }
        return new Date().toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric",
        })
    }

    getRatingValue(questionId) {
        const question = this.state.questions.find(
            q => q.question_id === questionId
        )
        if (question) {
            // Check lineRecord first
            if (question.lineRecord && question.lineRecord.data) {
                return question.lineRecord.data.rating || question.rating || ""
            }
            // Check direct rating property
            if (question.rating) {
                return question.rating
            }
        }
        return ""
    }

    onRatingChange(ev) {
        const questionId = parseInt(ev.target.dataset.questionId, 10)
        const rating = ev.target.value

        if (!this.state || !this.state.questions) {
            console.error(
                "[EvaluationWizard] State not available in onRatingChange"
            )
            return
        }

        const question = this.state.questions.find(
            q => q.question_id === questionId
        )
        if (!question) {
            console.warn(
                "[EvaluationWizard] Question not found for ID:",
                questionId
            )
            return
        }

        // Update local state immediately for UI responsiveness
        question.rating = rating
        if (question.lineRecord && question.lineRecord.data) {
            question.lineRecord.data.rating = rating
        }

        // Update via ORM if lineId exists (saved record)
        if (
            question.lineId &&
            typeof question.lineId === "number" &&
            question.lineId > 0
        ) {
            this.orm
                .write("hr.performance.evaluation.line", [question.lineId], {
                    rating: parseFloat(rating),
                })
                .catch(error => {
                    console.error(
                        "[EvaluationWizard] Error updating rating:",
                        error
                    )
                })
        }
    }

    getCommentValue(questionId) {
        const question = this.state.questions.find(
            q => q.question_id === questionId
        )
        if (question) {
            if (question.lineRecord && question.lineRecord.data) {
                return question.lineRecord.data.comment || ""
            }
            if (question.comment) {
                return question.comment
            }
        }
        return ""
    }

    handleBriefExplanationChange(ev) {
        const questionId = parseInt(ev.target.dataset.questionId, 10)
        const comment = ev.target.value

        const question = this.state.questions.find(
            q => q.question_id === questionId
        )
        if (!question) {
            console.warn(
                "[EvaluationWizard] Question not found for comment ID:",
                questionId
            )
            return
        }

        // Update local state
        question.comment = comment
        if (question.lineRecord && question.lineRecord.data) {
            question.lineRecord.data.comment = comment
        }

        // Update via ORM if lineId exists
        if (
            question.lineId &&
            typeof question.lineId === "number" &&
            question.lineId > 0
        ) {
            this.orm
                .write("hr.performance.evaluation.line", [question.lineId], {
                    comment: comment,
                })
                .catch(error => {
                    console.error(
                        "[EvaluationWizard] Error updating comment:",
                        error
                    )
                })
        }
    }

    handleCommentChange(ev) {
        const evaluationRecord = this.evaluationRecord
        if (evaluationRecord && evaluationRecord.update) {
            evaluationRecord.update({ note: ev.target.value })
        } else if (evaluationRecord && evaluationRecord.data) {
            evaluationRecord.data.note = ev.target.value
        }
    }

    get commentValue() {
        const evaluationRecord = this.evaluationRecord
        if (evaluationRecord && evaluationRecord.data) {
            return evaluationRecord.data.note || ""
        }
        return ""
    }

    async nextPage() {
        if (this.isLastPage) return

        // Validate current page questions
        const currentQuestions = this.currentQuestions
        const allRated = currentQuestions.every(q =>
            this.getRatingValue(q.question_id)
        )

        if (!allRated) {
            this.notification.add(
                "Please rate all questions on this page before proceeding.",
                {
                    type: "warning",
                    title: "Validation Error",
                }
            )
            return
        }

        this.state.currentPage++
    }

    previousPage() {
        if (this.state.currentPage > 0) {
            this.state.currentPage--
        }
    }

    async saveEvaluation(ev) {
        // Prevent default behavior and stop propagation
        if (ev) {
            ev.preventDefault()
            ev.stopPropagation()
            
            // Also check if button is disabled
            if (ev.target && ev.target.disabled) {
                return
            }
        }

        // Prevent multiple submissions - check class-level flag immediately (synchronous)
        if (this._isSaving) {
            console.log("[EvaluationWizard] Save blocked - already saving")
            return
        }

        console.log("[EvaluationWizard] Starting save evaluation")
        
        // Set flags immediately to prevent any race conditions
        this._isSaving = true
        this.state.isSaving = true

        // Validate all questions are rated
        const allRated = this.state.questions.every(q =>
            this.getRatingValue(q.question_id)
        )

        if (!allRated) {
            // Reset flags if validation fails
            this._isSaving = false
            this.state.isSaving = false
            this.notification.add(
                "Please rate all questions before saving the evaluation.",
                {
                    type: "warning",
                    title: "Validation Error",
                }
            )
            return
        }

        const evaluationRecord = this.evaluationRecord
        try {
            // Get evaluation ID or create new evaluation
            let evaluationId =
                evaluationRecord?.resId || evaluationRecord?.resIds?.[0]

            let isNewEvaluation = false
            if (!evaluationId) {
                // Check if evaluation already exists for this employee and evaluator
                const employeeId =
                    evaluationRecord?.data?.employee_id?.[0] ||
                    evaluationRecord?.data?.employee_id
                const evaluatorId =
                    evaluationRecord?.data?.evaluator_id?.[0] ||
                    evaluationRecord?.data?.evaluator_id ||
                    false

                if (employeeId && evaluatorId) {
                    const existingEvaluations = await this.orm.search(
                        "hr.performance.evaluation",
                        [
                            ["employee_id", "=", employeeId],
                            ["evaluator_id", "=", evaluatorId],
                        ],
                        { limit: 1 }
                    )

                    if (existingEvaluations && existingEvaluations.length > 0) {
                        // Use existing evaluation ID
                        evaluationId = existingEvaluations[0]
                        console.log(
                            "[EvaluationWizard] Found existing evaluation:",
                            evaluationId
                        )
                    }
                }

                if (!evaluationId) {
                    // Create the evaluation record first
                    isNewEvaluation = true
                    const evalData = {
                        employee_id: employeeId,
                        config_id:
                            evaluationRecord?.data?.config_id?.[0] ||
                            evaluationRecord?.data?.config_id,
                        evaluator_id: evaluatorId,
                        evaluator_category:
                            evaluationRecord?.data?.evaluator_category || false,
                        evaluation_date:
                            evaluationRecord?.data?.evaluation_date ||
                            new Date().toISOString().split("T")[0],
                        note: this.commentValue || "",
                        state: "draft",
                        line_ids: this.state.questions.map(q => [
                            0,
                            0,
                            {
                                question_id: q.question_id,
                                rating: parseFloat(
                                    this.getRatingValue(q.question_id)
                                ),
                                comment: q.lineRecord?.data?.comment || "",
                            },
                        ]),
                    }

                    evaluationId = await this.orm.create(
                        "hr.performance.evaluation",
                        [evalData]
                    )
                    evaluationId = evaluationId[0]
                }
            }

            // Update existing evaluation only if it's not a new one (new ones already have line_ids)
            if (!isNewEvaluation) {
                // Delete existing lines and create new ones
                const existingData = await this.orm.read(
                    "hr.performance.evaluation",
                    [evaluationId],
                    ["line_ids"]
                )

                if (
                    existingData &&
                    existingData[0] &&
                    existingData[0].line_ids
                ) {
                    // Delete existing lines
                    await this.orm.unlink(
                        "hr.performance.evaluation.line",
                        existingData[0].line_ids
                    )
                }

                // Create new lines
                const lineCommands = this.state.questions.map(q => [
                    0,
                    0,
                    {
                        question_id: q.question_id,
                        rating: parseFloat(this.getRatingValue(q.question_id)),
                        comment: q.lineRecord?.data?.comment || "",
                    },
                ])

                // Update evaluation with new lines and note
                await this.orm.write(
                    "hr.performance.evaluation",
                    [evaluationId],
                    {
                        line_ids: lineCommands,
                        note: this.commentValue || "",
                        evaluator_category:
                            evaluationRecord?.data?.evaluator_category || false,
                    }
                )
            } else {
                // For new evaluations, just update the note in case it changed
                await this.orm.write(
                    "hr.performance.evaluation",
                    [evaluationId],
                    {
                        note: this.commentValue || "",
                        evaluator_category:
                            evaluationRecord?.data?.evaluator_category || false,
                    }
                )
            }

            // Show success message
            this.notification.add("Evaluation saved successfully!", {
                type: "success",
            })

            // Reset saving flag before navigation
            this._isSaving = false
            this.state.isSaving = false

            // Navigate back to employee list
            await this.action.doAction(
                "hr_performance_360.action_employee_evaluation_python",
                {
                    clearBreadcrumbs: true,
                }
            )
        } catch (error) {
            console.error("[EvaluationWizard] Save error:", error)
            const errorMessage =
                error.data?.message ||
                error.data?.debug ||
                error.message ||
                "An error occurred while saving the evaluation."
            console.error(
                "[EvaluationWizard] Error details:",
                error.data || error
            )
            this.notification.add(errorMessage, {
                type: "danger",
                title: "Error",
            })
            // Reset saving flag on error
            this._isSaving = false
            this.state.isSaving = false
        }
    }
}

EvaluationWizardWidget.template = "hr_performance_360.EvaluationWizardWidget"
EvaluationWizardWidget.props = {
    ...standardFieldProps,
}

registry.category("fields").add("evaluation_wizard", {
    component: EvaluationWizardWidget,
    extractProps: ({ attrs }) => {
        return {}
    },
})
