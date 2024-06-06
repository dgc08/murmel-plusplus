;; murpp-mode.el --- Major mode for editing Murpp assembler files

(defvar murpp-mode-hook nil)

(defvar murpp-mode-map
  (let ((map (make-sparse-keymap)))
    ;; Define key bindings here, e.g.,
    ;; (define-key map (kbd "C-j") 'newline-and-indent)
    map)
  "Keymap for `murpp-mode'.")

(defvar murpp-mode-syntax-table
  (let ((syn-table (make-syntax-table)))
    ;; Comments start with ";" and go to the end of the line
    (modify-syntax-entry ?\; "<" syn-table)
    (modify-syntax-entry ?\n ">" syn-table)
    syn-table)
  "Syntax table for `murpp-mode'.")

(defconst murpp-font-lock-keywords
  (list
   ;; Keywords
   '("\\<\\(inc\\|dec\\|jmp\\|tst||\\hlt\\|movf\\|cpyf\\|jizf\\)\\>" . font-lock-keyword-face)
   ;; Registers
   '("\\<\\(s[0-9]+\\|r[0-9]+\\|io[0-9]+\\|e[0-9]+\\|)\\>" . font-lock-variable-name-face)
   ;; Labels
   '("^\\([a-zA-Z0-9_]+\\):" . font-lock-function-name-face))
  "Basic syntax highlighting for `murpp-mode'.")

(defun murpp-mode ()
  "Major mode for editing Murpp assembler files."
  (interactive)
  (kill-all-local-variables)
  (set-syntax-table murpp-mode-syntax-table)
  (use-local-map murpp-mode-map)
  (set (make-local-variable 'font-lock-defaults) '(murpp-font-lock-keywords))
  (set (make-local-variable 'indent-line-function) 'indent-relative)
  (setq major-mode 'murpp-mode)
  (setq mode-name "Murpp")
  (run-hooks 'murpp-mode-hook))

;; Associate .murpp files with murpp-mode
(add-to-list 'auto-mode-alist '("\\.murpp\\'" . murpp-mode))

(provide 'murpp-mode)

;;; murpp-mode.el ends here
