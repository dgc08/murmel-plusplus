;; murpp-mode.el --- Major mode for editing Murpp assembler files

(defvar murpp-mode-hook nil)

(defvar murpp-mode-map
  (let ((map (make-sparse-keymap)))
    ;; Define key bindings here, e.g.,
    ;; (define-key map (kbd "C-j") 'newline-and-indent)
    map)
  "Keymap for murpp-mode'.")

(defvar murpp-mode-syntax-table
  (let ((syn-table (make-syntax-table)))
    ;; Comments start with ";" and go to the end of the line
    (modify-syntax-entry ?\; "<" syn-table)
    (modify-syntax-entry ?\n ">" syn-table)
    syn-table)
  "Syntax table for murpp-mode'.")

(defconst murpp-font-lock-keywords
  '(
    ;; Control flow keywords
    ("\\<\\(inc\\|dec\\|jmp\\|tst\\|hlt\\)\\>"
     . font-lock-keyword-face)

    ;; Data movement keywords
    ("\\<\\(mov\\|cpy\\|jiz\\|jinz\\|jz\\|jnz\\|add\\|sub\\|mul\\|div\\|cpy\\|movz\\|cmp\\)\\>"
     . font-lock-keyword-face)

    ;; Macro and control keywords
    ("\\<\\(case\\|defmacro\\|putmacro\\|macro_end\\|include\\|push\\|pop\\|call\\|ret\\|syscall\\|scope\\|int\\)\\>"
     . font-lock-keyword-face)

    ;; Registers
    ("\\<\\(s[0-9]+\\|r[0-9]+\\|io[0-9]+\\|e[0-9]+\\|d[0-9]+\\|)\\>"
     . font-lock-variable-name-face)

    ;; Labels
    ("^\\([a-zA-Z0-9_.]+\\):"
     . font-lock-function-name-face)

    ;; Immediates
    ("#\\([0-9]+\\|.*\\)$"
     . font-lock-constant-face)
    )
  "Basic syntax highlighting for murpp-mode.")

(defun murpp-indent-line (&optional first-only unindented-ok)
  "Indent relative, with automatic indentation after colon."
 (interactive "P")
  (if (and abbrev-mode
           (eq (char-syntax (preceding-char)) ?w))
      (expand-abbrev))
  (let ((start-column (current-column))
        indent
        (deeper-indent nil))
    (save-excursion
      (beginning-of-line)
      ;; Check if the previous line ends with ":"
      (if (re-search-backward "^[^\n]" nil t)
          (progn
            (let ((end (save-excursion (forward-line 1) (point))))
              (move-to-column start-column)
              ;; Is start-column inside a tab on this line?
              (if (> (current-column) start-column)
                  (backward-char 1))
              (or (looking-at "[ \t]")
                  first-only
                  (skip-chars-forward "^ \t" end))
              (skip-chars-forward " \t" end)
              (or (= (point) end) (setq indent (current-column))))
            ;; Check if the previous line ends with ":"
            (end-of-line)
            (when (and (not first-only)
                       (looking-back ":\\s-*" (line-beginning-position)))
              (setq deeper-indent t)))))
    (cond (indent
           (let ((opoint (point-marker)))
             (indent-to (if deeper-indent (+ indent tab-width) indent) 0)
             (if (> opoint (point))
                 (goto-char opoint))
             (move-marker opoint nil)))
          (unindented-ok nil)
          (t (tab-to-tab-stop)))))

(defun murpp-mode ()
  "Major mode for editing Murpp assembler files."
  (interactive)
  (kill-all-local-variables)
  (set-syntax-table murpp-mode-syntax-table)
  (use-local-map murpp-mode-map)
  (set (make-local-variable 'font-lock-defaults) '(murpp-font-lock-keywords))
  (set (make-local-variable 'indent-line-function) 'murpp-indent-line)
  (setq comment-start ";") ; Set comment start syntax
  (setq comment-end "")    ; Set comment end syntax
  (setq major-mode 'murpp-mode)
  (setq mode-name "Murpp")
  (run-hooks 'murpp-mode-hook))

;; Associate .murpp files with murpp-mode
(add-to-list 'auto-mode-alist '("\\.murpp\\'" . murpp-mode))
(add-to-list 'auto-mode-alist '("\\.mur\\'" . murpp-mode))

(provide 'murpp-mode)
